#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import os
import pandas as pd
from loguru import logger

# FORMATTING_FILE = 'ColumnFormatting.json'  # Update with the actual path to your formatting file
""" This is a pervious iteration new version found below
def set_custom_excel_formatting(worksheet, workbook, df, details):

    logger.info("Formatting column widths and styles...")
    currency_format = workbook.add_format({"num_format": "$#,##0.00"})
    number_format = workbook.add_format({"num_format": "#,##0"})
    percentage_format = workbook.add_format({"num_format": "0%"})

    # Iterate through each column and set the width == the max length in that column. A padding length of 2 is also added.
    for i, col in enumerate(df.columns):
        column_len = max(df[col].astype(str).apply(len).max(), len(col)) + 2
        col_format = None
        if details.get(col) == "$":
            col_format = currency_format
        elif details.get(col) == "#":
            col_format = number_format
        elif details.get(col) == "%":
            col_format = percentage_format
        worksheet.set_column(i, i, column_len, col_format)
"""


def send_dataframes_to_file(frames, FORMATTING_FILE):
    """
    Takes a dict of dataframes, outputs them to Excel files, and optionally sends them to the default printer.
    """
    # Load column formatting details
    with open(FORMATTING_FILE) as json_data:
        column_details = json.load(json_data)

    args = os.sys.argv
    for filename, frame in frames.items():
        # Establish Excel output object and define column formats using a context manager
        with pd.ExcelWriter(filename, engine="xlsxwriter") as writer:
            frame.to_excel(writer, startrow=1, sheet_name="Sheet1", index=False)
            workbook = writer.book
            worksheet = writer.sheets["Sheet1"]
            set_custom_excel_formatting(worksheet, workbook, frame, column_details)
            logger.info("Worksheet formatted successfully.")

        logger.info("Worksheet saved successfully.")

        # Handling printing if applicable
        if len(args) > 1 and args[1] == "-np":
            logger.info("Bypassing print option due to '-np' option.")
        else:
            logger.info("Sending processed file to printer...")
            try:
                os.startfile(filename, "print")
            except FileNotFoundError as e:
                logger.error(f"File not found: {e}")


# Example usage:
# frames = {'output.xlsx': pd.DataFrame(data)}
# send_dataframes_to_file(frames, FORMATTING_FILE)


@logger.catch()
def set_custom_excel_formatting(df, writer, details):
    """By default this will expand column widths to display all content.
    Optionally a list of strings defining formats for alpha, numeric, currency or percentage
    may be specified per column. example: ['A','#','$','%'] would set the first 4 columns.
    """
    logger.info("formatting column widths and styles...")

    logger.info("Trying to create a formatted worksheet...")
    # Indicate workbook and worksheet for formatting
    workbook = writer.book
    worksheet = writer.sheets["Sheet1"]

    # Add some cell formats.
    currency_format = workbook.add_format({"num_format": "$#,##0.00"})
    nmbrfrmt = workbook.add_format({"num_format": "#,##0"})
    percntg = workbook.add_format({"num_format": "0%"})

    # Reduce the zoom a little
    worksheet.set_zoom(90)  # does not seem to have any effect

    # Iterate through each column and set the width == the max length in that column. A padding length of 2 is also added.
    for i, col in enumerate(df.columns):
        # find length of column i
        column_width = df[col].astype(str).str.len().max()
        # Setting the length if the column header is larger
        # than the max column value length
        column_width = max(column_width, len(col)) + 2
        if col in details.keys():
            # set the column length and format
            if details[col] == "A":
                worksheet.set_column(i, i, column_width)
            if details[col] == "#":
                worksheet.set_column(i, i, column_width, nmbrfrmt)
            if details[col] == "$":
                worksheet.set_column(i, i, column_width, currency_format)
            if details[col] == "%":
                worksheet.set_column(i, i, column_width, percntg)
        else:  # just set the width of the column
            worksheet.set_column(i, i, column_width)
    return True


"""

Show examples of modifying the Excel output generated by pandas

import pandas as pd
import numpy as np

from xlsxwriter.utility import xl_rowcol_to_cell


df = pd.read_excel("../in/excel-comp-datav2.xlsx")

# We need the number of rows in order to place the totals
number_rows = len(df.index)

# Add some summary data using the new assign functionality in pandas 0.16
df = df.assign(total=(df['Jan'] + df['Feb'] + df['Mar']))
df = df.assign(quota_pct=(1+(df['total'] - df['quota'])/df['quota']))

# Create a Pandas Excel writer using XlsxWriter as the engine.
# Save the unformatted results
writer_orig = pd.ExcelWriter('simple.xlsx', engine='xlsxwriter')
df.to_excel(writer_orig, index=False, sheet_name='report')
writer_orig.save()

# Create a Pandas Excel writer using XlsxWriter as the engine.
writer = pd.ExcelWriter('fancy.xlsx', engine='xlsxwriter')
df.to_excel(writer, index=False, sheet_name='report')

# Get access to the workbook and sheet
workbook = writer.book
worksheet = writer.sheets['report']

# Reduce the zoom a little
worksheet.set_zoom(90)

# Add a number format for cells with money.
money_fmt = workbook.add_format({'num_format': '$#,##0', 'bold': True})

# Add a percent format with 1 decimal point
percent_fmt = workbook.add_format({'num_format': '0.0%', 'bold': True})

# Total formatting
total_fmt = workbook.add_format({'align': 'right', 'num_format': '$#,##0',
                                 'bold': True, 'bottom':6})
# Total percent format
total_percent_fmt = workbook.add_format({'align': 'right', 'num_format': '0.0%',
                                         'bold': True, 'bottom':6})

# Format the columns by width and include number formats

# Account info columns
worksheet.set_column('B:D', 20)
# State column
worksheet.set_column('E:E', 5)
# Post code
worksheet.set_column('F:F', 10)

# Monthly columns
worksheet.set_column('G:K', 12, money_fmt)
# Quota percent columns
worksheet.set_column('L:L', 12, percent_fmt)

# Add total rows
for column in range(6, 11):
    # Determine where we will place the formula
    cell_location = xl_rowcol_to_cell(number_rows+1, column)
    # Get the range to use for the sum formula
    start_range = xl_rowcol_to_cell(1, column)
    end_range = xl_rowcol_to_cell(number_rows, column)
    # Construct and write the formula
    formula = "=SUM({:s}:{:s})".format(start_range, end_range)
    worksheet.write_formula(cell_location, formula, total_fmt)

# Add a total label
worksheet.write_string(number_rows+1, 5, "Total",total_fmt)
percent_formula = "=1+(K{0}-G{0})/G{0}".format(number_rows+2)
worksheet.write_formula(number_rows+1, 11, percent_formula, total_percent_fmt)

# Define our range for the color formatting
color_range = "L2:L{}".format(number_rows+1)

# Add a format. Light red fill with dark red text.
format1 = workbook.add_format({'bg_color': '#FFC7CE',
                               'font_color': '#9C0006'})

# Add a format. Green fill with dark green text.
format2 = workbook.add_format({'bg_color': '#C6EFCE',
                               'font_color': '#006100'})

# Highlight the top 5 values in Green
worksheet.conditional_format(color_range, {'type': 'top',
                                           'value': '5',
                                           'format': format2})

# Highlight the bottom 5 values in Red
worksheet.conditional_format(color_range, {'type': 'bottom',
                                           'value': '5',
                                           'format': format1})

writer.save()
"""
