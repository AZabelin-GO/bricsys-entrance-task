#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import argparse
import tempfile
import mysql.connector
from datetime import datetime

MYSQL_DATABASE = "ci_builds"
MYSQL_BUILD_HISTORY_TABLE = "build_history"
MYSQL_BUILD_HISTORY_STATS_TABLE = "build_history_stats"


def create_arg_parsers():
    mainParser = argparse.ArgumentParser(description="Script for analyzing build data")

    subParsers = mainParser.add_subparsers(title="Available actions", dest="action")

    databaseArgsParser = argparse.ArgumentParser(add_help=False)
    databaseArgsParser.add_argument("-H", metavar="host", default="localhost", dest="host",
                                    help="MySQL host. Default is 'localhost'")
    databaseArgsParser.add_argument("-P", metavar="port", default="3306", dest="port", type=int,
                                    help="MySQL port. Default is '3306'")
    databaseArgsParser.add_argument("-u", metavar="user", default="root", dest="user",
                                    help="MySQL user. Default is 'root'")
    databaseArgsParser.add_argument("-p", metavar="password", default="password", dest="password",
                                    help="MySQL password. Default is 'password'")

    initActionParser = subParsers.add_parser(name="init", parents=[databaseArgsParser],
                                             help="Check connection to database and create tables")

    parseActionParser = subParsers.add_parser(name="parse", parents=[databaseArgsParser],
                                              help="Parse data from file and upload it into database")
    parseActionParser.add_argument("DATA_FILE", nargs="+",
                                   help="CSV file with build history data")

    statActionParser = subParsers.add_parser(name="stat", parents=[databaseArgsParser],
                                             help="Calculate build stats")
    statActionParser.add_argument("-s", metavar="value", default=1, type=int, dest="sensitivity",
                                  help="Sensitivity of stats calculation. Default is '1'")

    return mainParser


def init_action(host, port, user, password):
    # Create database
    try:
        mysqlConnection = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password)

        mysqlCursor = mysqlConnection.cursor()

        sqlQuery = "CREATE DATABASE IF NOT EXISTS {}".format(MYSQL_DATABASE)
        mysqlCursor.execute(sqlQuery)

        mysqlConnection.commit()
        print("{} database created".format(MYSQL_DATABASE))
    except mysql.connector.Error as error:
        print("Failed to create database {}. Error: {}".format(MYSQL_DATABASE, error))
        mysqlConnection.rollback()
        if mysqlConnection.is_connected():
            mysqlCursor.close()
            mysqlConnection.close()
        exit(1)

    # Create table 'build_history'
    try:
        sqlQuery = "USE {}".format(MYSQL_DATABASE)
        mysqlCursor.execute(sqlQuery)

        sqlQuery = "CREATE TABLE IF NOT EXISTS {}(" \
                   "    test_id VARCHAR(255)," \
                   "    build_id INT," \
                   "    target VARCHAR(255)," \
                   "    branch_name VARCHAR(255)," \
                   "    build_status VARCHAR(255)," \
                   "    duration FLOAT," \
                   "    phys_memory INT," \
                   "    virt_memory INT," \
                   "    date BIGINT," \
                   "    test_node VARCHAR(255)" \
                   ")".format(MYSQL_BUILD_HISTORY_TABLE)
        mysqlCursor.execute(sqlQuery)

        mysqlConnection.commit()
        print("{} table created".format(MYSQL_BUILD_HISTORY_TABLE))
    except mysql.connector.Error as error:
        print("Failed to create table '{}'. Error: {}".format(MYSQL_BUILD_HISTORY_TABLE, error))
        mysqlConnection.rollback()
        if mysqlConnection.is_connected():
            mysqlCursor.close()
            mysqlConnection.close()
        exit(1)

    # Create table build_history_stats
    try:
        sqlQuery = "CREATE TABLE IF NOT EXISTS {}(" \
                   "    test_id VARCHAR(255)," \
                   "    build_id INT," \
                   "    duration FLOAT," \
                   "    date BIGINT," \
                   "    diff_from_lastbuild FLOAT" \
                   ")".format(MYSQL_BUILD_HISTORY_STATS_TABLE)
        mysqlCursor.execute(sqlQuery)

        mysqlConnection.commit()
        print("{} table created".format(MYSQL_BUILD_HISTORY_STATS_TABLE))
    except mysql.connector.Error as error:
        print("Failed to create table '{}'. Error: {}".format(MYSQL_BUILD_HISTORY_STATS_TABLE, error))
        mysqlConnection.rollback()
        if mysqlConnection.is_connected():
            mysqlCursor.close()
            mysqlConnection.close()
        exit(1)


def parse_action(host, port, user, password, files):

    for file in files:
        with(open(file, "r")) as originalDataFile:
            print("Parsing data from {}".format(file))
            # Get test_id from first line of file
            firstLine = originalDataFile.readline().lower()
            if firstLine.startswith("history of"):
                testId = firstLine.split()[2]
                tempFile = tempfile.NamedTemporaryFile(mode="w")
                # Remove redundant special symbols from original file
                for line in originalDataFile:
                    tempFile.write((line.replace(",", ".").replace("\t\t", "\t").replace("\t\n", "\n")))
                # Read data from normalised data file
                with(open(tempFile.name)) as normalisedDataFile:
                    csvDictReader = csv.DictReader(normalisedDataFile, delimiter="\t")
                    try:
                        mysqlConnection = mysql.connector.connect(
                            host=host,
                            port=port,
                            user=user,
                            password=password,
                            database=MYSQL_DATABASE,
                            autocommit=True
                        )

                        mysqlCursor = mysqlConnection.cursor()

                        for row in csvDictReader:
                            sqlQuery = "INSERT INTO {table} VALUES (" \
                                       "    '{test_id}'," \
                                       "    {build_id}," \
                                       "    '{target}'," \
                                       "    '{branch_name}'," \
                                       "    '{build_status}'," \
                                       "    {duration}," \
                                       "    {phys_memory}," \
                                       "    {virt_memory}," \
                                       "    {create_time}," \
                                       "    '{test_node}'" \
                                       ")".format(table=MYSQL_BUILD_HISTORY_TABLE, test_id=testId,
                                                  build_id=row["buildid"].strip(), target=row["target"].strip(),
                                                  branch_name=row["name"].strip(), build_status=row["status"].strip(),
                                                  duration=row["duration"].strip(),
                                                  phys_memory=row["physmemory"].strip(),
                                                  virt_memory=row["virtmemory"].strip(),
                                                  test_node=row["testnode"].strip(),
                                                  create_time=datetime.strptime(row["create time"].strip(),
                                                                                "%a %b %d %Y %H:%M:%S").timestamp(), )
                            mysqlCursor.execute(sqlQuery)
                    except mysql.connector.Error as error:
                        print("Failed to insert data: {}. Error: {}".format(sqlQuery, error))
                        mysqlConnection.rollback()
                        if mysqlConnection.is_connected():
                            mysqlCursor.close()
                            mysqlConnection.close()
                        exit(1)

                    tempFile.close()


def stat_action(host, port, user, password, sensitivity):
    try:
        test_ids = list()

        mysqlConnection = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=MYSQL_DATABASE,
            autocommit=True
        )

        mysqlCursor = mysqlConnection.cursor()

        # Get list of test_ids
        sqlQuery = "SELECT DISTINCT test_id FROM {}".format(MYSQL_BUILD_HISTORY_TABLE)
        mysqlCursor.execute(sqlQuery)
        for row in mysqlCursor:
            test_ids.append(row[0])

        # calculate stats for each test_id
        for test_id in test_ids:
            print("Calculating stats for {}".format(test_id))
            sqlQuery = "SELECT test_id, build_id, duration, date " \
                       "FROM {} WHERE test_id = '{}' and build_status = 'success' ORDER BY date ".format(MYSQL_BUILD_HISTORY_TABLE, test_id)
            mysqlCursor.execute(sqlQuery)
            results = mysqlCursor.fetchall()

            durationOfLastbuild = results[0][2]
            for row in results:
                difference = round(((row[2] - durationOfLastbuild) / durationOfLastbuild) * 100, 4)
                if abs(difference) >= sensitivity:
                    sqlQuery = "INSERT INTO {table} VALUES (" \
                               "'{test_id}'," \
                               "{build_id}," \
                               "{duration}," \
                               "{date}," \
                               "{difference}" \
                               ")".format(table=MYSQL_BUILD_HISTORY_STATS_TABLE, test_id=test_id, build_id=row[1],
                                          duration=row[2], date=row[3],
                                          difference=difference)
                    mysqlCursor.execute(sqlQuery)
                durationOfLastbuild = row[2]

    except mysql.connector.Error as error:
        print("Failed to fetch data from table {}. Error: {}".format(MYSQL_BUILD_HISTORY_TABLE, error))
        mysqlConnection.rollback()
        if mysqlConnection.is_connected():
            mysqlCursor.close()
            mysqlConnection.close()
        exit(1)
    finally:
        if mysqlConnection.is_connected():
            mysqlCursor.close()
            mysqlConnection.close()


def main():
    argsParser = create_arg_parsers()
    args = argsParser.parse_args()

    if args.action is None:
        argsParser.print_help()
    elif args.action == "init":
        init_action(args.host, args.port, args.user, args.password)
    elif args.action == "parse":
        parse_action(args.host, args.port, args.user, args.password, args.DATA_FILE)
    elif args.action == "stat":
        stat_action(args.host, args.port, args.user, args.password, args.sensitivity)


if __name__ == "__main__":
    main()
