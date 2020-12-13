#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cgi
import locale
import sys
import time
import traceback

import db_module

# from sensors_functions import iso_timestamp

METEO_FOLDER = "/home/pi/meteo/"
CAPTURES_FOLDER = METEO_FOLDER + "captures/"

form = cgi.FieldStorage()
locale.getdefaultlocale()
print("Content-type: text/html; charset=utf-8\n")

html = """<!DOCTYPE html>
<head>
    <title>Centrale météo St Benoît</title>
    <link rel="icon" type="image/svg+xml" href="html/favicon.svg">
</head>
<body>"""

try:
    # Connect or Create DB File
    conn = db_module.get_conn()
    curs = conn.cursor()
    curs.execute("SELECT name, priority, sensor_label, unit FROM sensors ORDER BY priority DESC;")
    sensors = curs.fetchall()
    oldest_date = -1
    sensor_list = "<table style=\"border: .15em solid black; border-collapse: collapse;\">\n" \
                  "<tr style=\"border: .1em solid black;\">\n" \
                  "\t<th style=\"padding-left: 1em;padding-right: 2em;\">Capteur</th>\n" \
                  "\t<th style=\"padding-left: 1em;padding-right: 2em;\">valeur</th>\n" \
                  "\t<td style=f\"padding-left: 1em;padding-right: 2em;\">date</td>\n" \
                  "\t<td style=\"padding-left: 1em;padding-right: 2em;\"></td>\n</tr>"
    camera_row = "<tr><td colspan=\"4\"><table style=\"text-align: center;\"><tr>"
    for sensor in sensors:
        (sensor_name, priority, sensor_label, unit) = sensor
        sensor_name = sensor_name.decode('ascii')

        if unit == "picture":  # Below 10, sensors are not displayed in top list (ie: pictures from camera)
            camera_row = camera_row \
                + "<td><img src=\"captures/grangette_2020-12-05Z12-00-07.jpg\" width=\"360em\" height=\"270em\" /><br/>" \
                + sensor_label + "<br/>2020-12-05Z12-00-07</td>"

        elif priority > 10:
            if priority > 70:
                style_row = "border: .069em solid lightgray;"
                style_value = "font-weight: bold;"
            elif priority < 35:
                style_row = "color: Silver; border: .069em solid lightgray;"
                style_value = ""
            else:
                style_row = "border: .069em solid lightgray;"
                style_value = ""

            # TODO Below request should be included as join in prior request
            curs.execute("""
                SELECT  epochtimestamp, measure
                FROM    raw_measures 
                WHERE   sensor = '""" + sensor_name + """'
                  AND   epochtimestamp = (  SELECT  MAX(epochtimestamp) 
                                            FROM    raw_measures 
                                            WHERE   sensor = '""" + sensor_name + """' );""")
            last_date_and_value = curs.fetchall()

            sensor_list = sensor_list + "<tr style=\"" + style_row + "\">"
            sensor_list = sensor_list + "\n\t<td style=\"padding-left: 1em;padding-right: 2em;\">" + sensor_label
            if len(last_date_and_value) > 0:
                (epochdate, value) = last_date_and_value[0]
                if oldest_date < epochdate:
                    oldest_date = epochdate
                # locale.getdefaultlocale()
                date_str = time.strftime('%-d/%m/%Y<br/>%H:%M:%S', time.localtime(epochdate))
                sensor_list = sensor_list \
                    + "</td>\n\t<td style=\"text-align: center;padding-left: 1em;padding-right: 2em;" \
                    + style_value + "\">" + str(value) + " " + unit + "</td>\n" \
                    + "\t<td style=\"padding-left: 1em;padding-right: 2em;font-size: x-small;text-align: center;\">" \
                    + date_str \
                    + "</td>\n\t<td style=\"padding-left: 1em;padding-right: 2em;\">" \
                    + "<a href=\"graph.svg?sensor=" + sensor_name + "&maxepoch=" + str(oldest_date) \
                    + "&width=980\">" \
                    + "<img src=\"graph.svg?sensor=" + sensor_name + "&maxepoch=" + str(oldest_date) \
                    + "&width=100\" style=\"width:100px;height:40px;\" /></a><td></tr>\n"
            else:
                sensor_list = sensor_list + "</td>\n<td style=\"text-align: center;padding-left: 1em;padding-right: 2em;" \
                    + style_value + "\">-</td>\n" \
                    + "<td style=\"padding-left: 1em;padding-right: 2em;font-size: x-small;text-align: center;\">-" \
                    + "</td>\n<td style=\"padding-left: 1em;padding-right: 2em;\"><td></tr>\n"

        # end of 'for sensor in sensors:'

    if oldest_date != -1:
        date_str = time.strftime('%A %-d %B - %H:%M', time.localtime(oldest_date))
        date_readings = "Dernier relevé le " + date_str
    else:
        date_readings = "Erreur de lecture de date!"

    sensor_list = sensor_list + """<tr style=\"border: .15em solid black;\">\n\t<td style=\"padding: 1em;\">
    <form action="index.html">
        <input type="submit" style=\"padding: 1.2em;\" value="Rafraichir" />
    </form></td>\n\t<td colspan="3">""" + date_readings + """</td></tr>""" + camera_row + """
      <td>
        <img src="captures/camera1_2020-10-07T15-45-08.jpg" width="360em" height="270em" /><br/>
        camera1<br/>2020-10-07T15-45-08</td>
    </tr></table></td></tr></table>"""

    html = html + "<h3>Dernières valeurs:</h2>" + sensor_list

except Exception as err:
    html = html + "<br/>Exception: {0}<br/>".format(err)
    print("Exception: {0}".format(err), file=sys.stderr)
    traceback.print_exc(file=sys.stderr)

html = html + "</body></html>"
print(html)
