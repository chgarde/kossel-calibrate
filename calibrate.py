import requests
import re
import time
import sys
import codecs
import random
import pickle
import matplotlib.pyplot as plt
import numpy as np
from sklearn import datasets, linear_model
from sklearn.metrics import mean_squared_error, r2_score
sys.stdout = codecs.getwriter('utf8')(sys.stdout)
sys.stderr = codecs.getwriter('utf8')(sys.stderr)


def uprint(text):
    print text.encode('ascii', 'ignore')


class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class UnexpectedAnswerError(Error):
    """Exception raised when an unexpected answer is sent back from the printer

    Attributes:
        expression -- input expression in which the error occurred
        message -- explanation of the error
    """

    def __init__(self, expression, message):
        self.expression = expression
        self.message = message


class Kossel:
    _url = ""

    def __init__(self, url):
        self._url = url

    def sendgcode(self, gcode):
        requests.get(self._url + "rr_gcode", {'gcode': gcode})
        result = unicode("")
        while len(result) == 0:
            r = requests.get(self._url + "rr_reply")
            r.encoding = "utf-8"
            result = r.text
            time.sleep(1)
        return result

    # GCODES to be sent
    def g32(self):
        return self._parse_G32(self.sendgcode("G32"))

    def m665(self):
        return self._parse_M665(self.sendgcode("M665"))

    def m666(self):
        return self._parse_M666(self.sendgcode("M666"))

    # config code to generate
    def m665_config(self, r):
        return "M665 R{delta_radius} L{diagonal} B{bed_radius} H{homed_height} X{x} Y{y}".format(**r)

    def m666_config(self, r):
        return "M666 X{ea_x} Y{ea_y} Z{ea_z}".format(**r)

    # internal classes
    def _parse_answer(self, s, regexp):
        p = re.compile(regexp)
        m = p.match(s)
        if m is not None:
            return m
        else:
            raise UnexpectedAnswerError(
                s, u"Could not match  : " + s + u"\nwith the pattern : " + regexp)

    def _parse_G32(self, s):
        m = self._parse_answer(
            s, u"Calibrated (\d+) factors using (\d+) points, deviation before (-?\d+\.\d+) after (-?\d+\.\d+)")
        return {
            "factors": int(m.group(1)),
            "points": int(m.group(2)),
            "deviation_before": float(m.group(3)),
            "deviation_after": float(m.group(4)),
            "gap": float(m.group(4)) - float(m.group(3))
        }

    def _parse_M665(self, s):
        m = self._parse_answer(
            s, u"Diagonal (-?\d+\.\d+), delta radius (-?\d+\.\d+), homed height (-?\d+\.\d+), bed radius (-?\d+\.\d+), X (-?\d+\.\d+)\u00B0, Y (-?\d+\.\d+)\u00B0, Z (-?\d+\.\d+)\u00B0")
        return {
            "diagonal": float(m.group(1)),
            "delta_radius": float(m.group(2)),
            "homed_height": float(m.group(3)),
            "bed_radius": float(m.group(4)),
            "x": float(m.group(5)),
            "y": float(m.group(6)),
            "z": float(m.group(7))
        }

    def _parse_M666(self, s):
        m = self._parse_answer(
            s, "Endstop adjustments X(-?\d+\.\d+) Y(-?\d+\.\d+) Z(-?\d+\.\d+), tilt X(-?\d+\.\d+)% Y(-?\d+\.\d+)%")
        return {
            "ea_x": float(m.group(1)),
            "ea_y": float(m.group(2)),
            "ea_z": float(m.group(3)),
            "tx": float(m.group(4)),
            "ty": float(m.group(5))
        }


class KosselTestStatic(Kossel):
    _fake_results = {
        "G32": u"Calibrated 6 factors using 13 points, deviation before 0.186 after 0.157",
        "M665": u"Diagonal 215.000, delta radius 104.760, homed height 234.554, bed radius 85.0, X 0.643\u00B0, Y -0.069\u00B0, Z 0.000\u00B0",
        "M666": u"Endstop adjustments X0.54 Y-0.85 Z0.30, tilt X0.00% Y0.00%"
    }

    def sendgcode(self, gcode):
        return self._fake_results[gcode]


class KosselTestRandom(Kossel):

    def g32(self):
        b = random.uniform(0.1, 0.2)
        a = random.uniform(0.1, 0.2)
        return {
            "factors": 6,
            "points": 13,
            "deviation_before": b,
            "deviation_after": a,
            "gap": b - a
        }

    def m665(self):
        return {
            "diagonal": 215.0,
            "delta_radius": random.uniform(104.0, 106.0),
            "homed_height": random.uniform(233, 234),
            "bed_radius": 85.0,
            "x": random.uniform(-2, 2),
            "y": random.uniform(-2, 2),
            "z": random.uniform(-2, 2)
        }

    def m666(self):
        return {
            "ea_x": random.uniform(-2, 2),
            "ea_y": random.uniform(-2, 2),
            "ea_z": random.uniform(-2, 2),
            "tx": random.uniform(-2, 2),
            "ty": random.uniform(-2, 2)
        }


def main():
    #raw_input("WARNING : make sure you disable the web console otherwise this program will not work. Press enter when ready...")
    kossel = Kossel("http://minikossel-beefdeadfeed.local/")



    tr32 = []
    tr665 = []
    tr666 = []
    try:

        # Getting back the objects:
        with open('objs.pkl') as f:  # Python 3: open(..., 'rb')
             tr32, tr665, tr666 = pickle.load(f)

        for i in range(1, 6):
            r32 = kossel.g32()
            tr32.append(r32)
            print r32
            print "Deviation before/after : {deviation_before}/{deviation_after} gap = {gap}".format(**r32)
            r665 = kossel.m665()
            tr665.append(r665)
            print r665
            r666 = kossel.m666()
            tr666.append(r666)
            print r666

            # Saving the objects:
            with open('objs.pkl', 'w') as f:  # Python 3: open(..., 'wb')
                pickle.dump([tr32, tr665, tr666], f)

        c1 = ["gap"]
        c2 = ["delta_radius", "homed_height", "x", "y", "z"]

        def myplot(zone, item, fields):
            # Create linear regression object
            regr = linear_model.LinearRegression()
            # Train the model using the training sets
            plt.subplot(zone)
            plt.grid(True)
            for f in fields:
                ly = list(map(lambda x: x.get(f), item))
                lx = map(lambda x: [x], range(0, len(ly)))
                print ly
                print lx
                regr.fit(lx, ly)
                ly_pred = regr.predict(lx)
                plt.scatter(lx, ly,  color='black')
                plt.plot(lx, ly_pred, color='blue', linewidth=3)
                plt.xticks(())
                plt.yticks(())
                plt.ylabel(f)

        plt.figure(1)
        myplot(331, tr32, ["gap"])
        # col2 : M665
        myplot(332, tr665, ["delta_radius"])
        myplot(333, tr665, ["homed_height"])
        myplot(334, tr665, ["x"])
        myplot(335, tr665, ["y"])

        # col3 : M666
        myplot(337, tr666, ["ea_x"])
        myplot(338, tr666, ["ea_y"])
        myplot(339, tr666, ["ea_z"])
        plt.show()

    except UnexpectedAnswerError as e:
        print "An unexpected answer was sent from the printer"
        print e.message
        print e.expression
        raise


main()
