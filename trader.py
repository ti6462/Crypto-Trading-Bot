#!/usr/bin/python3
import logging
import logging.handlers
import gdax
import time
import json
import traceback
import yaml
import sys
import decimal
import bookkeeper
import sched
import dateutil
import datetime
import pprint



# Uncomment for sandbox work #
############################
"""
with open('configuration/credentials/sandbox_creds.txt') as creds:
    credentials = json.load(creds)
auth_client = gdax.AuthenticatedClient(credentials['api_key'], credentials['api_secret'], credentials['api_passphrase'], api_url="https://api-public.sandbox.gdax.com")
"""

# Uncomment for live trades #
#############################

with open('configuration/credentials/gdax_api_creds.txt') as creds:
    credentials = json.load(creds)

auth_client = gdax.AuthenticatedClient(credentials['api_key'], credentials['api_secret'], credentials['api_passphrase'])


def menu_structure(prompt, *args):
    choices = []
    print(prompt)
    for c in args:
        if isinstance(c, list):
            for x in c:
                choices.append(x)
        else:
            choices.append(c)

    for e, c in enumerate(choices):
        print(e, ":", c)
    while True:
        try:
            choice = choices[int(input('Enter a choice:'))]
            print(choice)
            break
        except Exception:
            print('Invalid Entry. Try again.')
    return choice



def average(numbers):
    numbers = [x for x in numbers if x is not None]
    return float(sum(numbers)) / (len(numbers))


def get_products():
    unwanted_products = ['EUR', 'GBP']
    print("GDAX Available Products:")
    try:
        products = auth_client.get_products()
        if "message" in products:
            raise Exception(products)

        for index, product in enumerate(products):
            if product["quote_currency"] in unwanted_products:
                products.pop(index)
        for index, product in enumerate(products):
            print(index, product['id'])
        choice = get_non_negative_int('Please Select a product: ')
        print(products[choice]["id"])
        return (products[choice])

    except Exception as e:
        raise


def get_non_negative_int(prompt):
    while True:
        try:
            value = int(input(prompt))
        except ValueError:
            print("Sorry, please try again...")
            continue
        if value < 0:
            print("Fucking retard, try again")
            continue
        else:
            break
    return value


def get_non_negative_float(prompt):
    while True:
        try:
            value = float(input(prompt))
        except ValueError:
            print("Sorry, please try again...")
            continue
        if value < 0:
            print("Listen, we do things in absolutes.  Give us a positive number")
            continue
        else:
            break
    return value





def get_cmv(product):
    # obtains current market value for a selected product and returns only the price

    try:
        data = auth_client.get_product_ticker(product)
        if 'message' in data:
            raise Exception(data)
        return float(data['price'])

    except Exception as e:
        raise


def extract_pricing_data(histdata, times, product, detail, indicator_hours, baseline_hours, buy_down_trigger_hrs,
                         sell_up_trigger_hrs,
                         buy_up_trigger_hrs, sma_sell_change_trigger_hours, sma_sell_constraint_trigger_hours):
    sma_indicator = []
    sma_baseline = []
    buy_down_hour = []
    buy_down_hour_calc = []
    sell_down_hour = []
    sell_down_hour_calc = []
    sell_up_hour = []
    sell_up_hour_calc = []
    buy_up_hour = []
    buy_up_hour_calc = []
    sma_sell_change_hour = []
    sma_sell_change_hour_calc = []
    sma_sell_constraint_hour = []
    sma_sell_constraint_hour_calc = []
    full_price_list = []

    # SMA Indicator Data
    for key in histdata:
        if key[0] >= times['starthour_indicator'] and key[0] < times['endhour_indicator']:
            collector = key[0], key[4]
            if detail == "high":
                print('{} {} {}'.format(time.strftime("%m-%d-%y %I:%M %p %Z", time.localtime(key[0])), key[4], product))
            sma_indicator.append(collector)

            # SMA Baseline Data
    if detail == 'high':
        print('\n Baseline RAW DATA \n' + '-' * 25)

    for key in histdata:  # this loops through each date and price in the list and 'collects' the output if it meets the criteria
        if key[0] >= times['starthour_baseline'] and key[0] < times['endhour_baseline']:
            collector1 = key[0], key[4]  # time, price (i'm assuming)
            if detail == 'high':
                print('{} {} {}'.format(time.strftime("%m-%d-%y %I:%M %p %Z", time.localtime(key[0])), key[4], product))
            sma_baseline.append(collector1)




            # Grabbing Long Range data into a single list of prices, which will be used to compute multiple SMAs later on
    for key in histdata:
        if key[0] >= times['starthour_long_baseline'] and key[0] < times['endhour_long_baseline']:
            price_collector = key[4]
            full_price_list.append(price_collector)




            # Buy Down Trigger Hours

    print('\n Buy Down Trigger Hours \n' + '-' * 25)
    try:

        for key in histdata:
            if key[0] == times['buy_down_start_hour'] or key[0] == times['hour_over_end']:
                collector2 = key[0], key[4]
                printvar = key[4]
                buy_down_hour_calc.append(printvar)
                if detail == 'high':
                    print('{} {} {}'.format(time.strftime("%m-%d-%y %I:%M %p %Z", time.localtime(key[0])), key[4],
                                            product))
                buy_down_hour.append(collector2)
        print("Buffer Hours: " + str(buy_down_trigger_hrs))
        print("Percentage Change: " + str(round((buy_down_hour_calc[1] / buy_down_hour_calc[0] - 1) * 100, 2)) + "%")
    except Exception as e:
        print("Buy down Trigger aborted:", e)
        buy_down_hour = None

    # Sell Down Trigger Hours

    print('\n Sell Down Trigger Hours \n' + '-' * 25)
    try:
        for key in histdata:
            if key[0] == times['previous_hour'] or key[0] == times['hour_over_end']:
                collector3 = key[0], key[4]
                printvar0 = key[4]
                sell_down_hour_calc.append(printvar0)
                if detail == 'high':
                    print('{} {} {}'.format(time.strftime("%m-%d-%y %I:%M %p %Z", time.localtime(key[0])), key[4],
                                            product))
                sell_down_hour.append(collector3)
        print("Buffer Hours: 1")
        print("Percentage Change: " + str(round((sell_down_hour_calc[1] / sell_down_hour_calc[0] - 1) * 100, 2)) + "%")
    except Exception as e:
        print("Sell Down Trigger aborted :", e)
        sell_down_hour = None

    # Sell Up Trigger Hours

    print('\n Sell Up Trigger Hours \n' + '-' * 25)
    try:
        for key in histdata:
            if key[0] == times['sell_up_start_hour'] or key[0] == times['hour_over_end']:
                collector4 = key[0], key[4]
                printvar1 = key[4]
                sell_up_hour_calc.append(printvar1)
                if detail == 'high':
                    print('{} {} {}'.format(time.strftime("%m-%d-%y %I:%M %p %Z", time.localtime(key[0])), key[4],
                                            product))
                sell_up_hour.append(collector4)
        print("Buffer Hours: " + str(sell_up_trigger_hrs))
        print("Percentage Change: " + str(round((sell_up_hour_calc[1] / sell_up_hour_calc[0] - 1) * 100, 2)) + "%")
    except Exception as e:
        print("Sell Up Trigger aborted:", e)
        sell_up_hour = None

    # Buy Up Trigger Hours

    print('\n Buy Up Trigger Hours \n' + '-' * 25)
    try:
        for key in histdata:
            if key[0] == times['buy_up_start_hour'] or key[0] == times['hour_over_end']:
                collector5 = key[0], key[4]
                printvar2 = key[4]
                buy_up_hour_calc.append(printvar2)
                if detail == 'high':
                    print('{} {} {}'.format(time.strftime("%m-%d-%y %I:%M %p %Z", time.localtime(key[0])), key[4],
                                            product))
                buy_up_hour.append(collector5)
        print("Buffer Hours: " + str(buy_up_trigger_hrs))
        print("Percentage Change: " + str(round((buy_up_hour_calc[1] / buy_up_hour_calc[0] - 1) * 100, 2)) + "%")
    except Exception as e:
        print("Buy Up Trigger aborted:", e)
        buy_up_hour = None

    # SMA Sell Change Hours

    print('\n SMA Sell Change Hours \n' + '-' * 25)
    try:
        for key in histdata:
            if key[0] == times['sma_sell_change_hour'] or key[0] == times['hour_over_end']:
                collector6 = key[0], key[4]
                printvar3 = key[4]
                sma_sell_change_hour_calc.append(printvar3)
                if detail == 'high':
                    print('{} {} {}'.format(time.strftime("%m-%d-%y %I:%M %p %Z", time.localtime(key[0])), key[4],
                                            product))
                sma_sell_change_hour.append(collector6)
        print("Buffer Hours: " + str(sma_sell_change_trigger_hours))
        print("Percentage Change: " + str(
            round((sma_sell_change_hour_calc[1] / sma_sell_change_hour_calc[0] - 1) * 100, 2)) + "%")
    except Exception as e:
        print("SMA Sell Change aborted:", e)
        sma_sell_change_hour = None

    # SMA Sell Constraint Hours

    try:

        print('\n SMA Sell Constraint Hours \n' + '-' * 25)

        for key in histdata:
            if key[0] == times['sma_sell_constraint_hour'] or key[0] == times['hour_over_end']:
                collector7 = key[0], key[4]
                printvar4 = key[4]
                sma_sell_constraint_hour_calc.append(printvar4)
                if detail == 'high':
                    print('{} {} {}'.format(time.strftime("%m-%d-%y %I:%M %p %Z", time.localtime(key[0])), key[4],
                                            product))
                sma_sell_constraint_hour.append(collector7)
        print("Buffer Hours: " + str(sma_sell_constraint_trigger_hours))
        print("Percentage Change: " + str(
            round((sma_sell_constraint_hour_calc[1] / sma_sell_constraint_hour_calc[0] - 1) * 100, 2)) + "%")
    except Exception as e:
        print("SMA Sell Constraint aborted", e)
        sma_sell_constraint_hour = None

    return sma_indicator, sma_baseline, buy_down_hour, sell_down_hour, sell_up_hour, buy_up_hour, sma_sell_change_hour, sma_sell_constraint_hour, full_price_list  # OUTPUT HERE IS CALLED his_pric_data


def compute_sma(his_pric_data, baseline_long_hours, indicator_long_hours, sma_indicator_V3, sma_baseline_V3):
    ##Compute SMA
    ### SMA10 and SMA25 are returned as alist of tuples


    sma_indicator = his_pric_data[0]
    list = [x[1] for x in sma_indicator]
    sma_baseline = his_pric_data[1]
    list1 = [x[1] for x in sma_baseline]

    if his_pric_data[2] != None:
        buy_down_hour = his_pric_data[2]
        list2 = [x[1] for x in buy_down_hour]
        buy_down_hour_diff = ((list2[1] - list2[0]) / list2[0]) * 100
    else:
        buy_down_hour_diff = None

    if his_pric_data[3] != None:
        sell_down_hour = his_pric_data[3]
        list3 = [x[1] for x in sell_down_hour]
        sell_down_hour_diff = ((list3[1] - list3[0]) / list3[0]) * 100
    else:
        sell_down_hour_diff = None

    if his_pric_data[4] != None:
        sell_up_hour = his_pric_data[4]
        list4 = [x[1] for x in sell_up_hour]
        sell_up_hour_diff = ((list4[1] - list4[0]) / list4[0]) * 100
    else:
        sell_up_hour_diff = None

    if his_pric_data[5] != None:
        buy_up_hour = his_pric_data[5]
        list5 = [x[1] for x in buy_up_hour]
        buy_up_hour_diff = ((list5[1] - list5[0]) / list5[0]) * 100
    else:
        buy_up_hour_diff = None

    if his_pric_data[6] != None:
        sma_sell_chg_hour = his_pric_data[6]
        list6 = [x[1] for x in sma_sell_chg_hour]
        sma_sell_change_diff = ((list6[1] - list6[0]) / list6[0]) * 100
    else:
        sma_sell_change_diff = None

    if his_pric_data[7] != None:
        sma_sell_const_hour = his_pric_data[7]
        list7 = [x[1] for x in sma_sell_const_hour]
        sma_sell_const_diff = ((list7[1] - list7[0]) / list7[0]) * 100
    else:
        sma_sell_const_diff = None

    # COMPUTE ANY NEW SMAS HERE

    # computing the bear market SMAs
    full_price_list = his_pric_data[
        8]  # full list of prices (right side is most recent) going back as many hours as the long baseline

    sma_indicator_long_list = full_price_list[-indicator_long_hours:]
    sma_baseline_long_list = full_price_list[-baseline_long_hours:]

    sma_indicator_avg_long = average(sma_indicator_long_list)
    sma_baseline_avg_long = average(sma_baseline_long_list)
    sma_long_variance = (sma_indicator_avg_long / sma_baseline_avg_long - 1) * 100

    sma_indicator_list_V3 = full_price_list[-sma_indicator_V3:]
    sma_baseline_list_V3 = full_price_list[-sma_baseline_V3:]

    sma_indicator_avg_V3 = average(sma_indicator_list_V3)
    sma_baseline_avg_V3 = average(sma_baseline_list_V3)
    sma_variance_V3 = (sma_indicator_avg_V3 / sma_baseline_avg_V3 - 1) * 100

    sum = 0
    sum1 = 0

    for item in list:
        sum = item + sum
    for item1 in list1:
        sum1 = item1 + sum1

    return (sum / float(len(list)), sum1 / float(len(list1)), buy_down_hour_diff, sell_down_hour_diff,
            sell_up_hour_diff, buy_up_hour_diff, sma_sell_change_diff, sma_sell_const_diff, sma_long_variance,
            sma_variance_V3)


def advice(sma, product, detail, t, cmv, buy_threshold, sell_threshold, buy_down_trigger, sell_down_trigger,
           sell_up_trigger,
           buy_up_trigger, sma_sell_change_threshold, sell_threshold_adjust, sma_sell_constraint, sell_up_trigger_stop,
           sell_up_trigger2,
           sell_up_trigger_stop2, sma_buy_change_threshold, buy_threshold_adjust, buy_down_last_trade,
           buy_down_low_profit,
           sell_up_after_trade_time, sell_up_after_trade_profit, sell_up_after_trade_adjust, abandon_sell_time,
           abandon_sell_trigger, abandon_sell_adjust, sma_threshold_down, buy_down_trigger_adjusted,
           sma_sell_constraint2,
           buy_down_release1, buy_down_release2, buy_down_sell_constraint, sell_up_advice_time, sell_up_advice_change,
           sma_buy_constraint,
           bear_market_on_switch, bear_threshold, buy_threshold_V3, sell_threshold_V3, bear_profit, bear_sell_time,
           variance_off, self):
    buy_down_hour_return = sma[2]
    buy_down_hour_return_error = False
    if buy_down_hour_return == None:
        buy_down_hour_return = 0
        buy_down_hour_return_error = True

    sell_down_hour_return = sma[3]
    sell_down_hour_return_error = False
    if sell_down_hour_return == None:
        sell_down_hour_return = 0
        sell_down_hour_return_error = True

    sell_up_hour_return = sma[4]
    sell_up_hour_return_error = False
    if sell_up_hour_return == None:
        sell_up_hour_return = 0
        sell_up_hour_return_error = True

    buy_up_hour_return = sma[5]
    buy_up_hour_return_error = False
    if buy_up_hour_return == None:
        buy_up_hour_return = 0
        buy_up_hour_return_error = True

    sma_change_return = sma[6]
    sma_change_return_error = False
    if sma_change_return == None:
        sma_change_return = 0
        sma_change_return_error = True

    sma_sell_constraint_return = sma[7]
    sma_sell_constraint_return_error = False
    if sma_sell_constraint_return == None:
        sma_sell_constraint_return = 0
        sma_sell_constraint_return_error = True

    diff = sma[0] - sma[1]
    sma_diff_percent = diff / sma[1] * 100

    if self.cycle_count == 0:
        self.last_trade_price = cmv
        self.last_advice_price = cmv

    trade_diff = (cmv / self.last_trade_price - 1) * 100
    advice_diff = (cmv / self.last_advice_price - 1) * 100

    self.cycle_count += 1

    # Calculating the new SMAs
    sma_long_variance = sma[8]
    sma_variance_V3 = sma[9]

    #  Creating markets --
    if self.cycle_count != 0 and self.advice_detail == "Sell_Up_After_Trade" and self.market != 101 \
            and sma_long_variance < -bear_threshold:  # turning off SMAs to lock in a profitable trade
        self.market = 101
    elif self.cycle_count != 0 and (self.market == 101 or self.market == 100) and sma_variance_V3 > variance_off and \
      sma_variance_V3 < 8 and sma_long_variance < -bear_threshold:  # turning off SMAs to lock in a profitable trade
        self.market = 100
    elif sma_long_variance < 0 and abs(sma_long_variance) > bear_threshold and bear_market_on_switch == 1:
        self.market = 3
    else:
        self.market = 0

    print("\nCMV:{}".format(cmv))
    print("SMA Indicator:{}".format(sma[0]))
    print("SMA Baseline:{}".format(sma[1]))
    print("SMA Variance: {0:.2f}%".format(sma_diff_percent))
    print('Hrly Change: {0:.2f}%'.format(sell_down_hour_return))

    print('\n''Last Trade Time:  ' + str(self.last_trade_time))
    print('Last Trade Price:  ' + str(self.last_trade_price))
    print('Last Advice:  ' + str(self.advice_log))
    print('Last Advice Detail:  ' + str(self.advice_detail))
    print('\n''Last Advice Time:  ' + str(self.last_advice_time))
    print('Last Advice Price:  ' + str(self.last_advice_price))
    print('trade diff:  ' + str(trade_diff))

    print('\n'"SMA Long Variance: {0:.2f}%".format(sma_long_variance))
    print('Market (0 = normal; 3 = bear):  ' + str(self.market))
    print("SMA Variance Bear Market: {0:.2f}%".format(sma_variance_V3))

    # Buy Down Trigger (normal case)
    if buy_down_hour_return_error != True and self.advice_detail != "Buy_Down_Trigger" and buy_down_hour_return < 0 and \
                    abs(buy_down_hour_return) >= buy_down_trigger and sma_diff_percent > -sma_threshold_down:
        # Ex: (HoHr -6%) <= (Buy Trigger -5.8%) would trigger a buy

        print('ADVICE: BUY: Buy Down Trigger')
        if self.advice_log != "Buy":
            trade_log = 1
        else:
            trade_log = 0
        if self.advice_detail != "Buy_Down_Trigger":
            advice_change_log = 1
        else:
            advice_change_log = 0
        self.advice_log = "Buy"
        self.advice_detail = "Buy_Down_Trigger"
        self.gdax_limit_order("buy")

    # Buy Down Trigger (extreme case)
    elif buy_down_hour_return_error != True and buy_down_hour_return < 0 and \
                    abs(buy_down_hour_return) >= buy_down_trigger_adjusted and sma_diff_percent < -sma_threshold_down:
        # Ex: If the market is experiencing an extreme drop, then increase the threshold for the buy down trigger.

        print('ADVICE: BUY: Buy Down Trigger')
        if self.advice_log != "Buy":
            trade_log = 1
        else:
            trade_log = 0
        if self.advice_detail != "Buy_Down_Trigger":
            advice_change_log = 1
        else:
            advice_change_log = 0
        self.advice_log = "Buy"
        self.advice_detail = "Buy_Down_Trigger"
        self.gdax_limit_order("buy")
    # Buy Down Trigger HODL
    elif buy_down_hour_return_error != True and self.advice_detail == "Buy_Down_Trigger" and self.last_advice_time <= buy_down_last_trade and \
                    advice_diff < (buy_down_low_profit - 2):
        # Keeps the buy down trigger active until market bounces or X hours expire.

        print('ADVICE: BUY: Buy Down Trigger')
        if self.advice_log != "Buy":
            trade_log = 1
        else:
            trade_log = 0
        if self.advice_detail != "Buy_Down_Trigger":
            advice_change_log = 1
        else:
            advice_change_log = 0
        self.advice_log = "Buy"
        self.advice_detail = "Buy_Down_Trigger"
        self.gdax_limit_order("buy")
    # Buy Down Trigger Release
    elif buy_down_hour_return_error != True and self.advice_detail == "Buy_Down_Trigger" and sma[1] > sma[0] and abs(
            sma_diff_percent) > buy_down_release1 and \
                    abs(sma_diff_percent) < buy_down_release2 and sma_change_return < buy_down_sell_constraint:
        # A custom release mechanism for buy down in the event that SMA doesn't release the buy down position on its own

        print('ADVICE: SELL: Buy Down Trigger Release')
        if self.advice_log != "Sell":
            trade_log = 1
        else:
            trade_log = 0
        if self.advice_detail != "Buy_Down_Release":
            advice_change_log = 1
        else:
            advice_change_log = 0
        self.advice_log = "Sell"
        self.advice_detail = "Buy_Down_Release"
        self.gdax_limit_order("sell")
    # Sell Up After Trade
    elif self.advice_log == "Buy" and self.last_trade_time <= sell_up_after_trade_time and \
                    trade_diff > sell_up_after_trade_profit and sma_change_return < sell_up_after_trade_adjust:
        # This sells your stack if you make X profit in X hours after your trade. Applies in a flat to down market.

        print('ADVICE: SELL: Sell Up After Trade')
        if self.advice_log != "Sell":
            trade_log = 1
        else:
            trade_log = 0
        if self.advice_detail != "Sell_Up_After_Trade":
            advice_change_log = 1
        else:
            advice_change_log = 0
        self.advice_log = "Sell"
        self.advice_detail = "Sell_Up_After_Trade"
        self.gdax_limit_order("sell")

    # Abandon Sell
    elif self.advice_log == "Sell" and self.last_trade_time <= abandon_sell_time and \
                    sma_sell_constraint_return > abandon_sell_trigger and sma_change_return < -abandon_sell_adjust:
        # Buys back in if you sold recently but the market starts heading back up.

        print('ADVICE: BUY: Abandon Sell')
        if self.advice_log != "Buy":
            trade_log = 1
        else:
            trade_log = 0
        if self.advice_detail != "Abandon Sell":
            advice_change_log = 1
        else:
            advice_change_log = 0
        self.advice_log = "Buy"
        self.advice_detail = "Abandon Sell"
        self.gdax_limit_order("buy")

    # Sell Down Trigger
    elif sell_down_hour_return_error != True and sell_down_hour_return < 0 and abs(
            sell_down_hour_return) >= sell_down_trigger:
        # Ex: (HoHr -4.9%) <= (Sell Trigger -4.6%) and (HoHr -4.9%) >= (Buy trigger -5.8%) would trigger a sell

        print('ADVICE: SELL: Sell Down Trigger')
        if self.advice_log != "Sell":
            trade_log = 1
        else:
            trade_log = 0
        if self.advice_detail != "Sell_Down_Trigger":
            advice_change_log = 1
        else:
            advice_change_log = 0
        self.advice_log = "Sell"
        self.advice_detail = "Sell_Down_Trigger"
        self.gdax_limit_order("sell")
    # Sell Up Trigger
    elif sell_up_hour_return_error != True and (
                sell_up_hour_return > 0 and abs(sell_up_hour_return) > sell_up_trigger and abs(
            sell_up_hour_return) < sell_up_trigger_stop) \
            or (sell_up_hour_return > 0 and abs(sell_up_hour_return) > sell_up_trigger2 and abs(
                sell_up_hour_return) < sell_up_trigger_stop2):

        print('ADVICE: SELL: Sell Up Trigger')
        if self.advice_log != "Sell":
            trade_log = 1
        else:
            trade_log = 0
        if self.advice_detail != "Sell_Up_Trigger":
            advice_change_log = 1
        else:
            advice_change_log = 0
        self.advice_log = "Sell"
        self.advice_detail = "Sell_Up_Trigger"
        self.gdax_limit_order("sell")

    # Sell Up Trigger HODL
    elif sell_up_hour_return_error != True and self.advice_detail == "Sell_Up_Trigger" and self.last_advice_time <= sell_up_advice_time and \
                    advice_diff > (sell_up_advice_change - 6):

        print('ADVICE: SELL: Sell Up Trigger')
        if self.advice_log != "Sell":
            trade_log = 1
        else:
            trade_log = 0
        if self.advice_detail != "Sell_Up_Trigger":
            advice_change_log = 1
        else:
            advice_change_log = 0
        self.advice_log = "Sell"
        self.advice_detail = "Sell_Up_Trigger"
        self.gdax_limit_order("sell")
    # Buy Up Trigger
    elif buy_down_hour_return_error != True and buy_up_hour_return > 0 and abs(buy_up_hour_return) >= buy_up_trigger:

        print('ADVICE: BUY: Buy Up Trigger')
        if self.advice_log != "Buy":
            trade_log = 1
        else:
            trade_log = 0
        if self.advice_detail != "Buy_Up_Trigger":
            advice_change_log = 1
        else:
            advice_change_log = 0
        self.advice_log = "Buy"
        self.advice_detail = "Buy_Up_Trigger"
        self.gdax_limit_order("buy")

    # SMA Threshold Down (Adjusted)
    elif self.market == 0 and sma[1] > sma[0] and abs(sma_diff_percent) > sell_threshold_adjust and \
                    sma_sell_constraint_return < sma_sell_constraint and sma_change_return > sma_sell_change_threshold \
            and sell_down_hour_return > -sma_sell_constraint2:
        # if SMA Baseline > SMA Indicator AND absolute value difference > sell_threshold = SELL!

        print('ADVICE: SELL: SMA THRESHOLD DOWN - ADJUSTED')
        if self.advice_log != "Sell":
            trade_log = 1
        else:
            trade_log = 0
        if self.advice_detail != "SMA_Threshold_Down_Adjusted":
            advice_change_log = 1
        else:
            advice_change_log = 0
        self.advice_log = "Sell"
        self.advice_detail = "SMA_Threshold_Down_Adjusted"
        self.gdax_limit_order("sell")

    # SMA Threshold Down
    elif self.market == 0 and sma[1] > sma[0] and abs(
            sma_diff_percent) > sell_threshold and sma_sell_constraint_return < sma_sell_constraint and \
                    sma_change_return < sma_sell_change_threshold and sell_down_hour_return > -sma_sell_constraint2:
        # if SMA Baseline > SMA Indicator AND absolute value difference > sell_threshold = SELL!

        print('ADVICE: SELL: SMA THRESHOLD DOWN')
        if self.advice_log != "Sell":
            trade_log = 1
        else:
            trade_log = 0
        if self.advice_detail != "SMA_Threshold_Down":
            advice_change_log = 1
        else:
            advice_change_log = 0
        self.advice_log = "Sell"
        self.advice_detail = "SMA_Threshold_Down"
        self.gdax_limit_order("sell")


    # SMA Threshold Up
    elif self.market == 0 and sma[0] > sma[1] and abs(sma_diff_percent) > buy_threshold and \
                    sma_change_return > -sma_buy_change_threshold and sell_down_hour_return < sma_buy_constraint:
        # if SMA Indicator > SMA Baseline  AND absolute value difference > buy threshold = BUY!

        print('ADVICE: BUY: SMA THRESHOLD UP')
        if self.advice_log != "Buy":
            trade_log = 1
        else:
            trade_log = 0
        if self.advice_detail != "SMA_Threshold_Up":
            advice_change_log = 1
        else:
            advice_change_log = 0
        self.advice_log = "Buy"
        self.advice_detail = "SMA_Threshold_Up"
        self.gdax_limit_order("buy")


    # SMA Threshold Up (Adjusted)
    elif self.market == 0 and sma[0] > sma[1] and abs(sma_diff_percent) > buy_threshold_adjust and \
                    sma_change_return < -sma_buy_change_threshold and sell_down_hour_return < sma_buy_constraint:
        # if SMA Indicator > SMA Baseline  AND absolute value difference > buy threshold = BUY!

        print('ADVICE: BUY: SMA THRESHOLD UP - ADJUSTED')
        if self.advice_log != "Buy":
            trade_log = 1
        else:
            trade_log = 0
        if self.advice_detail != "SMA_Threshold_Up_Adjusted":
            advice_change_log = 1
        else:
            advice_change_log = 0
        self.advice_log = "Buy"
        self.advice_detail = "SMA_Threshold_Up_Adjusted"

        self.gdax_limit_order("buy")

    #######################BEAR MARKET###############################
    # SMA Sell - Threshold Down - BEAR
    elif self.market == 3 and sma_variance_V3 < 0 and abs(
            sma_variance_V3) > sell_threshold_V3 and sma_sell_constraint_return < sma_sell_constraint \
            and sell_down_hour_return > -sma_sell_constraint2:
        # if SMA Baseline > SMA Indicator AND absolute value difference > sell_threshold = SELL!
        print('ADVICE: SELL: SMA THRESHOLD DOWN BEAR')
        if self.advice_log != "Sell":
            trade_log = 1
        else:
            trade_log = 0
        if self.advice_detail != "SMA_Threshold_Down_Bear":
            advice_change_log = 1
        else:
            advice_change_log = 0
        self.advice_log = "Sell"
        self.advice_detail = "SMA_Threshold_Down_Bear"
        self.gdax_limit_order("sell")


        # SMA Buy - Threshold Up - BEAR
    elif self.market == 3 and sma_variance_V3 > 0 and abs(
            sma_variance_V3) > buy_threshold_V3 and sell_down_hour_return < sma_buy_constraint:
        # if SMA Indicator > SMA Baseline  AND absolute value difference > buy threshold = BUY!

        print('ADVICE: BUY: SMA THRESHOLD UP BEAR')
        if self.advice_log != "Buy":
            trade_log = 1
        else:
            trade_log = 0
        if self.advice_detail != "SMA_Threshold_Up_Bear":
            advice_change_log = 1
        else:
            advice_change_log = 0
        self.advice_log = "Buy"
        self.advice_detail = "SMA_Threshold_Up_Bear"
        self.gdax_limit_order("buy")


    # SELL UP AFTER TRADE - BEAR MARKET
    elif self.market == 3 and self.advice_log == "Buy" and self.last_trade_time >= bear_sell_time and \
                    trade_diff > bear_profit:
        # This sells your stack if you make X profit in X hours after your trade. Applies in a bear market.

        print('ADVICE: SELL: Sell Up After Trade')
        if self.advice_log != "Sell":
            trade_log = 1
        else:
            trade_log = 0
        if self.advice_detail != "Sell_Up_After_Trade":
            advice_change_log = 1
        else:
            advice_change_log = 0
        self.advice_log = "Sell"
        self.advice_detail = "Sell_Up_After_Trade"
        self.gdax_limit_order("sell")




    else:
        print('ADVICE: No Action Taken')
        if self.advice_detail != "No_Action_Taken":
            advice_change_log = 1
        else:
            advice_change_log = 0
        self.advice_detail = "No_Action_Taken"
        trade_log = 0

    if trade_log == 1:
        self.last_trade_price = cmv

    if advice_change_log == 1:
        self.last_advice_price = cmv

    if self.last_trade_time == 0 or trade_log == 1:
        self.last_trade_time = 1
    else:
        self.last_trade_time += 1

    if self.last_advice_time == 0 or advice_change_log == 1:
        self.last_advice_time = 1
    else:
        self.last_advice_time += 1


def detail_level():
    while True:
        try:
            detail_l = {"1": "high", "2": "low"}[input("Detail Level? \nEnter 1 for High or 2 for low:")]
        except KeyError:
            print("Invalid Entry. Try again.")
        else:
            print(detail_l)
            break

    return detail_l


def getaccounts():
    """Pull account data.  This pulls the entire account list from GDAX.com using the API.  The loop enumerates the list of dictionaries so I can have an index to refer to the list of dictionaries
    by.  It also has an IF statement that checks if the dictionary/key combo have a value that is the same as the products you select to trade at program boot.  It then pulls the correct dictionary and stores
     it in the variable for the next loop."""

    try:
        accounts = auth_client.get_accounts()
        if 'message' in accounts:
            raise Exception(accounts)

    except Exception as e:
        raise

    return accounts


class trading_pair():
    def __init__(self, product_holder):
        self.id = product_holder["id"]
        self.base_currency = product_holder["base_currency"]
        self.quote_currency = product_holder["quote_currency"]
        self.base_min_size = decimal.Decimal(product_holder["base_min_size"])
        self.base_max_size = decimal.Decimal(product_holder["base_max_size"])
        self.quote_increment = decimal.Decimal(product_holder["quote_increment"])
        self.quote_account = account_collector[self.quote_currency]
        self.base_account = account_collector[self.base_currency]
        self.quote_currency_spec = currency_spec_dict[self.quote_currency]
        self.base_currency_spec = currency_spec_dict[self.base_currency]
        self.buy_orders = []
        self.sell_orders = []
        self.base_allocation = None
        self.quote_allocation = None
        self.advice_summary = "Buy"
        self.advice_detail = "N/A"
        self.advice_log = "Buy"
        self.market = 0
        self.last_trade_time = 0
        self.last_trade_price = 1
        self.last_advice_price = 1
        self.last_advice_time = 0
        self.advice_change_log = 0
        self.cycle_count = 0
        self.trade_track_file_path = "trade_tracking/" + self.id + ".csv"

        # imported_candles
        self.candles = []
        self.missing_candles = []

        # Limit Order Persistent Variables
        self.lo_allowable_slippage = 0
        self.lo_allowable_duration = 0
        self.lo_attempt_tracker = 0
        self.lo_followup_counter = 0
        self.lo_initial_placement_price = 0
        self.lo_current_placement_price = 0
        self.lo_initial_order_size = 0
        self.lo_current_order_size = 0
        self.lo_time_tracker = 0
        self.lo_order_book = None
        self.lo_current_fill = 0
        self.lo_fill_orders = {"closed":{}, "open": {}}

        # Call to bookkeeper to allocate account balances
        bookkeeper.reload_allocations(self)

        try:
            with open('configuration/trading_pairs/' + self.id + ".yaml", 'r') as self.config:
                answer = menu_structure("Configuration file found for {}. Load?".format(self.id), "Yes", "No")
                if answer == "Yes":
                    self.config_set_file(yaml.load(self.config))
                else:
                    self.config_set_input()
        except KeyError:
            print("Configuration file error.  Please check the file. Switching to manual input.")
            self.config_set_input()
        except Exception as e:
            root.critical("Something went wrong, please check config file. \n", e)
            self.config_set_input()

    def config_set_file(self, config):
        try:
            self.indicator_hours = config['Indicator Hours']
            self.baseline_hours = config['Baseline Hours']
            self.buy_threshold = config['Buy Threshold %']
            self.sell_threshold = config['Sell Threshold %']
            self.buy_down_trigger = config['Buy Down Trigger']
            self.buy_down_trigger_hrs = config['Buy Down Trigger Buffer']
            self.sell_down_trigger = config['Sell Down Trigger']
            self.sma_sell_change_trigger_hours = config['SMA Sell Change Trigger Hours']
            self.sma_sell_change_threshold = config['SMA Sell Change Threshold']
            self.sell_threshold_adjust = config['SMA Sell Adjust Threshold']
            self.sma_buy_change_threshold = config['SMA Buy Change Threshold']
            self.buy_threshold_adjust = config['SMA Buy Adjust Threshold']
            self.sell_up_trigger = config['Sell Up Trigger']
            self.sell_up_trigger_stop = config['Sell Up Trigger Stop']
            self.sell_up_trigger2 = config['Sell Up Trigger2']
            self.sell_up_trigger_stop2 = config['Sell Up Trigger Stop 2']
            self.sell_up_trigger_hrs = config['Sell Up Trigger Buffer']
            self.buy_up_trigger = config['Buy Up Trigger']
            self.buy_up_trigger_hrs = config['Buy Up Trigger Buffer']
            self.sma_sell_constraint = config['SMA Sell Constraint']
            self.sma_sell_constraint_trigger_hours = config['SMA Sell Constraint Buffer']
            self.lagtime = config['Lag Time']
            self.frequency = config['Frequency']
            self.priority = len(trading_pair_collector)

            self.buy_down_last_trade = config['Buy Down Last Trade']
            self.buy_down_low_profit = config['Buy Down Low Profit']

            self.sell_up_after_trade_time = config['Sell Up After Trade Time']
            self.sell_up_after_trade_profit = config['Sell Up After Trade Profit']
            self.sell_up_after_trade_adjust = config['Sell Up After Trade Adjust']

            self.abandon_sell_time = config['Abandon Sell Time']
            self.abandon_sell_trigger = config['Abandon Sell Trigger']
            self.abandon_sell_adjust = config['Abandon Sell Adjust']

            self.sma_threshold_down = config['SMA Threshold Down']
            self.buy_down_trigger_adjusted = config['Buy Down Trigger Adjusted']
            self.sma_sell_constraint2 = config['SMA Sell Constraint2']

            self.sma_buy_constraint = config['SMA Buy Constraint']

            self.buy_down_release1 = config['Buy Down Release 1']
            self.buy_down_release2 = config['Buy Down Release 2']
            self.buy_down_sell_constraint = config['Buy Down Sell Constraint']

            self.sell_up_advice_time = config['Sell Up Advice Time']
            self.sell_up_advice_change = config['Sell Up Advice Change']

            self.indicator_long_hours = config['Indicator Long Hours']
            self.baseline_long_hours = config['Baseline Long Hours']

            self.bear_market_on_switch = config['Bear Market On Switch']
            self.bear_threshold = config['Bear Threshold']
            self.sma_indicator_V3 = config['SMA Indicator V3']
            self.sma_baseline_V3 = config['SMA Baseline V3']
            self.buy_threshold_V3 = config['Buy Threshold V3']
            self.sell_threshold_V3 = config['Sell Threshold V3']

            self.bear_profit = config['Bear Profit']
            self.bear_sell_time = config['Bear Sell Time']
            self.variance_off = config['Variance Off']

            self.lo_allowable_duration = config['limit order duration']
            self.lo_allowable_slippage = decimal.Decimal(config['limit order slippage'])

        except KeyError as e:
            root.warning("{} was not found in the config file.  Please adjust the file before reload.".format(e))
            raise

    def config_set_input(self):
        self.indicator_hours = get_non_negative_int("Enter indicator in Hours \n Hours:")
        while self.indicator_hours < 1:
            print("Must be 1 hour or greater. Try again.")
            self.indicator_hours = get_non_negative_int("Enter indicator in Hours \n Hours:")
        self.baseline_hours = get_non_negative_int("Enter baseline in Hours \n Hours:")
        while self.baseline_hours < 1:
            print("Must be 1 hour or greater. Try again.")
            self.baseline_hours = get_non_negative_int("Enter baseline in Hours \n Hours:")
        self.buy_threshold = get_non_negative_float("Please enter the THRESHOLD to cross before placing a BUY "
                                                    "order on SMA advice. \n Threshold %:")
        self.sell_threshold = get_non_negative_float("Please enter the THRESHOLD to cross before placing a SELL "
                                                     "order on SMA advice. \n Threshold %:")
        self.buy_down_trigger = get_non_negative_float("Please enter the percentage DECREASE "
                                                       "that triggers an immediate BUY (BUY DOWN TRIGGER) \n Threshold %:")
        self.buy_down_trigger_hrs = get_non_negative_int(
            "Enter the BUFFER in hours for the BUY DOWN TRIGGER \n Example: at 8pm, a 2 hour buffer would be 7pm vs 5pm  \n Hours:")
        self.sell_down_trigger = get_non_negative_float("Please enter the percentage DECREASE "
                                                        "that triggers an immediate SELL (SELL DOWN TRIGGER) \n Threshold %:")
        self.sma_sell_change_trigger_hours = get_non_negative_int("Enter the SMA SELL ADJUST TRIGGER HOURS  \n Hours:")
        self.sma_sell_change_threshold = get_non_negative_float("Enter the SMA SELL CHANGE THRESHOLD  \n Hours:")
        self.sell_threshold_adjust = get_non_negative_float("Enter the SMA SELL THRESHOLD ADJUSTMENT \n Threshold %:")

        self.sma_buy_change_threshold = get_non_negative_float(
            "Enter the SMA BUY CHANGE THRESHOLD (PROGRAM CONVERTS TO NEGATIVE) \n Hours:")

        self.buy_threshold_adjust = get_non_negative_float("Enter the SMA BUY THRESHOLD ADJUSTMENT \n Threshold %:")

        self.indicator_long_hours = get_non_negative_int("Enter indicator LONG in Hours \n Hours:")
        while self.indicator_long_hours < 1:
            print("Must be 1 hour or greater. Try again.")
            self.indicator_long_hours = get_non_negative_int("Enter indicator LONG in Hours \n Hours:")

        self.baseline_long_hours = get_non_negative_int("Enter baseline LONG in Hours \n Hours:")
        while self.baseline_long_hours < 1:
            print("Must be 1 hour or greater. Try again.")
            self.baseline_long_hours = get_non_negative_int("Enter baseline LONG in Hours \n Hours:")

        self.sell_up_trigger = get_non_negative_float("Please enter the percentage INCREASE "
                                                      "that triggers an immediate SELL (SELL UP TRIGGER) \n Threshold %:")
        self.sell_up_trigger_stop = get_non_negative_float(
            "Please enter the SELL UP TRIGGER STOP  (SELL UP TRIGGER STOP) \n Threshold %:")
        self.sell_up_trigger2 = get_non_negative_float(
            "Please enter the SELL UP TRIGGER 2  (SELL UP TRIGGER 2) \n Threshold %:")
        self.sell_up_trigger_stop2 = get_non_negative_float(
            "Please enter the sell_up_trigger_stop2  (SELL UP TRIGGER STOP 2) \n Threshold %:")
        self.sell_up_trigger_hrs = get_non_negative_int(
            "Enter the BUFFER in hours for the SELL UP TRIGGER .\n Example: at 8pm, a 2 hour buffer would be 7pm vs 5pm  \n Hours:")
        self.buy_up_trigger = get_non_negative_float("Please enter the percentage INCREASE "
                                                     "that triggers an immediate BUY (BUY UP TRIGGER)\n Threshold %:")
        self.buy_up_trigger_hrs = get_non_negative_int(
            "Enter the BUFFER in hours for the BUY UP TRIGGER \n Example: at 8pm, a 2 hour buffer would be 7pm vs 5pm  \n Hours:")
        self.sma_sell_constraint = get_non_negative_float("Please enter the percentage INCREASE "
                                                          "that stops SMA sell from firing (SMA SELL CONSTRAINT)\n Threshold %:")
        self.sma_sell_constraint_trigger_hours = get_non_negative_int(
            "Please enter the SMA SELL CONSTRAINT HOURS \n Hours:")

        self.buy_down_last_trade = get_non_negative_int("Enter BUY DOWN LAST TRADE \n  Hours: ")
        self.buy_down_low_profit = get_non_negative_float("Enter BUY DOWN LOW PROFIT \n Threshold %")

        self.sell_up_after_trade_time = get_non_negative_int("Enter SELL UP AFTER TRADE TIME \n  Hours: ")
        self.sell_up_after_trade_profit = get_non_negative_float("Enter SELL UP AFTER TRADE PROFIT \n Threshold %")
        self.sell_up_after_trade_adjust = get_non_negative_float("Enter SELL UP AFTER TRADE ADJUST \n Threshold %")

        self.abandon_sell_time = get_non_negative_int("Enter ABANDON SELL TIME \n  Hours: ")
        self.abandon_sell_trigger = get_non_negative_float("Enter ABANDON SELL TRIGGER \n Threshold %")
        self.abandon_sell_adjust = get_non_negative_float("Enter ABANDON SELL ADJUST \n Threshold %")

        self.sma_threshold_down = get_non_negative_float("Enter SMA THRESHOLD DOWN \n Threshold %")
        self.buy_down_trigger_adjusted = get_non_negative_float("Enter BUY DOWN TRIGGER (ADJUSTED) \n Threshold %")
        self.sma_sell_constraint2 = get_non_negative_float("Enter SMA SELL CONSTRAINT 2 \n Threshold %")

        self.sma_buy_constraint = get_non_negative_float("Enter SMA BUY CONSTRAINT \n Threshold %")

        self.buy_down_release1 = get_non_negative_float("Enter BUY DOWN RELEASE 1 \n Threshold %")
        self.buy_down_release2 = get_non_negative_float("Enter BUY DOWN RELEASE 2 \n Threshold %")
        self.buy_down_sell_constraint = get_non_negative_float("Enter BUY DOWN SELL CONSTRAINT \n Threshold %")

        self.sell_up_advice_time = get_non_negative_int("Enter SELL UP ADVICE TIME \n  Hours: ")
        self.sell_up_advice_change = get_non_negative_float("Enter SELL UP ADVICE CHANGE \n Threshold %")

        self.bear_market_on_switch = get_non_negative_int("Turn Bear Market On  \n (Binary y/n):")
        self.bear_threshold = get_non_negative_float("Enter BEAR MARKET THRESHOLD \n THRESHOLD: %")
        self.sma_indicator_V3 = get_non_negative_int("Enter SMA INDICATOR BEAR MARKET \n Hours:")
        self.sma_baseline_V3 = get_non_negative_int("Enter SMA BASELINE BEAR MARKET \n Hours:")
        self.buy_threshold_V3 = get_non_negative_float("Enter BEAR MARKET BUY \n Threshold %")
        self.sell_threshold_V3 = get_non_negative_float("Enter BEAR MARKET SELL \n Threshold %")

        self.bear_profit = get_non_negative_float("Enter BEAR PROFIT to trigger sell \n Threshold %")
        self.bear_sell_time = get_non_negative_int("Enter BEAR SELL TIME (time before considering market exit) \n Hours:")
        self.variance_off = get_non_negative_float("Enter VARIANCE OFF threshold that turns off bear sell \n Threshold %")

        self.lo_allowable_duration = get_non_negative_float("Enter allowable LO duration before MO execution. \n Seconds:")
        self.lo_allowable_slippage = get_non_negative_float("Enter allowable LO slippage before MO execution. (1 = 1%) \n Slippage: ")

        self.lagtime = get_non_negative_int("Enter lag time in Hours")
        self.frequency = get_non_negative_int(
            "Define frequency (minutes) in which you want to trade this product will run\n Minutes:")

    def gdax_limit_order(self, side):
        self.lo_order_book = auth_client.get_product_order_book(self.id, level=1)
        best_bid = decimal.Decimal(self.lo_order_book['bids'][0][0])
        best_ask = decimal.Decimal(self.lo_order_book['asks'][0][0])
        if best_ask - best_bid >= .01:
            best_bid += decimal.Decimal(.01)
            best_ask -= decimal.Decimal(.01)
        dustless_quote_allocation = self.quote_allocation - (self.quote_allocation % self.quote_currency_spec.min_size)
        dustless_base_allocation = self.base_allocation - (self.base_allocation % self.base_currency_spec.min_size)

        if side == "buy" and dustless_quote_allocation >= self.quote_currency_spec.min_size:
            best_price = best_bid - (best_bid % self.quote_currency_spec.min_size)
            size = dustless_quote_allocation / best_price
            size = size - (size % self.base_currency_spec.min_size)
            gdax_client = auth_client.buy

        elif side == "sell" and dustless_base_allocation >= self.base_currency_spec.min_size:
            best_price = best_ask - (best_ask % self.quote_currency_spec.min_size)
            size = dustless_base_allocation
            gdax_client = auth_client.sell

        else:
            return

        # Place the buy order with GDAX
        try:
            status = gdax_client(price=str(best_price), size=str(size), product_id=self.id, type='limit',
                                     post_only=True)
            if 'message' in status:
                raise Exception(status)
            if status['status'] == "canceled":
                root.warning(auth_client.get_order(status['id']))


        except Exception as e:
            root.warning("{} Order placement error: {} : {}".format(self.id, e, status))
            root.warning("Retry in 5 seconds")
            queue.enter(5, 1, self.gdax_limit_order, (side,))

            return

        root.info("{} {} Limit Order placed with Coinbase "
                     "{:0.7f} {} @ {:0.2f} {}".format(self.id, side, size, self.base_currency, best_price, self.quote_currency))
        root.debug("Coinbase Resonse: {}".format(status))

        self.lo_fill_orders["open"][status['id']] = status

        if self.lo_attempt_tracker == 0:
            self.lo_current_fill = 0
            self.lo_time_tracker = time.time()
            self.lo_initial_placement_price = best_price
            self.lo_current_placement_price = best_price
            self.lo_current_order_size = decimal.Decimal(status['size'])
            self.lo_initial_order_size = decimal.Decimal(status['size'])

        else:
            self.lo_current_order_size += (self.lo_current_fill + size) - self.lo_current_order_size
            self.lo_current_placement_price = best_price

        #schedule follow up
        queue.enterabs(time.time()+1,1, self.gdax_limit_reprice)
        self.lo_attempt_tracker += 1

    def gdax_limit_reprice(self):
        def update_order(order_id):
            try:
                order_status = auth_client.get_order(order_id)
                root.debug("Order Update response: {}".format(order_status))

                if order_status == None:
                    root.warning("The {} order was deleted outside of the BOT".format(self.id))
                    return None

                if 'message' in order_status:
                    raise Exception(order_status)

                return order_status

            except Exception as e:
                root.debug("gdax_limit_reprice order {} : {}".format(order_id, e))
                return


        def update_order_book():
            try:
                order_book = auth_client.get_product_order_book(self.id, level=1)
                root.debug("Order Book Update response: {}".format(order_book))
                if 'message' in order_book:
                    raise Exception(order_book)


                return order_book

            except Exception as e:
                root.warning(e)
                return

        def order_completed():
            total_fill = 0
            total_value = 0
            total_fees = 0
            fill_orders = []
            elapsed_time = time.time() - self.lo_time_tracker
            side = None
            for key, order in self.lo_fill_orders['closed'].items():
                total_fill += dec(order['filled_size'])
                total_value += dec(order['executed_value'])
                total_fees += dec(order['fill_fees'])
                fill_orders.append(order['id'])
                side = order['side']

            if total_fill > 0:
                price = total_value / total_fill
                quote_market_slippage = self.lo_current_placement_price - self.lo_initial_placement_price
                total_slippage_quote = total_value - (self.lo_initial_placement_price * self.lo_initial_order_size)
                total_slippage_base = total_fill - self.lo_initial_order_size

                root.info("****** {} Order completed *******\n"
                         "\t\t{} Limit order of {:0.7f} for {:0.2f} {} has been successfully filled.\n"
                         "\t\tElapsed Time: {} sec  Order repriced: {} times\n"
                         "\t\tQuote Market slippage: {:0.2f} {}\n"
                         "\t\tQuote order impact: {:0.2f} {}  Base order impact {:0.7f} {}"
                             .format(self.id, self.id, total_fill, total_value, self.quote_currency_spec.id,
                                     round(elapsed_time, 2), self.lo_attempt_tracker - 1, quote_market_slippage,
                                     self.quote_currency_spec.id, total_slippage_quote, self.quote_currency_spec.id,
                                     total_slippage_base, self.base_currency_spec.id))

                bookkeeper.record_trade(self.id, side, total_fill, price, total_value, total_fees,
                                        total_value - total_fees, self.advice_detail, fill_orders, self.base_allocation,
                                        self.quote_allocation, self.trade_track_file_path, self)


        dec = decimal.Decimal

        for key, order in list(self.lo_fill_orders["open"].items()):

            order_update = update_order(order["id"])
            order_book_update = update_order_book()
            side = order['side']
            if order_update != order:

                if order_update == {"message": "NotFound"} or order_update is None:

                    self.lo_fill_orders['closed'][key] = self.lo_fill_orders['open'].pop(key)
                    root.debug("Deleted {} from OPEN DICT" .format(key))

                    continue

                if self.lo_attempt_tracker > 0:

                    if order_update['status'] == 'rejected' and order_update['reject_reason'] == 'post only':
                        root.warning("The orderbook moved too rapidly and the replacement order was rejected. Retrying..")
                        self.lo_fill_orders['closed'][key] = self.lo_fill_orders['open'].pop(key)
                        root.debug("Deleted {} from OPEN DICT".format(key))
                        queue.enter(1, 1, self.gdax_limit_order, (side,))

                        continue


                if dec(order_update["filled_size"]) != dec(order["filled_size"]):
                    filled_difference = dec(order_update['filled_size']) - dec(order['filled_size'])
                    fees_difference = dec(order_update['fill_fees']) - dec(order['fill_fees'])
                    executed_value_diff = dec(order_update['executed_value']) - dec(order['executed_value'])
                    self.lo_current_fill += filled_difference
                    root.info("{:0.7f} {} Limit Order Fill Received. Remaining: {:0.7f} of {:0.7f} {} ".format(filled_difference,
                                                                                                                  self.base_currency,
                                                                                                                  self.lo_current_order_size - self.lo_current_fill,
                                                                                                                  self.lo_current_order_size, self.base_currency))
                    if side == "buy":
                        bookkeeper.base_buy_allocation_update(self, filled_difference, executed_value_diff, fees_difference)

                    elif side == "sell":
                        bookkeeper.base_sell_allocation_update(self, executed_value_diff, filled_difference,
                                                               fees_difference)

                if order_update['status'] == 'done' or order_update['status'] == 'canceled' and order['status'] == 'open':
                    self.lo_fill_orders["open"][key] = order_update
                    self.lo_fill_orders['closed'][key] = self.lo_fill_orders['open'].pop(key)

                elif order_update['status'] == 'open' and order['status'] == 'pending':
                    root.info("{} {} order status has moved from pending to open.".format(self.id, side))
                    self.lo_fill_orders["open"][key] = order_update

                else:
                    self.lo_fill_orders['open'][key] = order_update

#                elif order_update['status'] == 'open' and order['status'] == 'open':
#                    order = order_update

            # If the timer has run out and there are open orders, cancel them and queue follow up.
            elif time.time() - self.lo_time_tracker > self.lo_allowable_duration and key in self.lo_fill_orders['open']:

                status = auth_client.cancel_order(key)
                if type(status) is dict:
                    if status['message'] == 'Order already done':
                        queue.enter(0, 1, self.gdax_limit_reprice)
                        return

                root.info("{} {} Limit Order elapsed time has exceeded {} seconds. "
                             "Canceling outstanding limit order.\n"
                             "Executing a Market Order.".format(self.id, side, self.lo_allowable_duration))

                queue.enter(1, 1, self.gdax_limit_reprice)

                return

            elif side == "buy" and ((dec(order_book_update["bids"][0][0]) / self.lo_initial_placement_price)
                                    - 1) * 100 > self.lo_allowable_slippage \
                    or side == "sell" and ((dec(order_book_update['asks'][0][0]) / self.lo_initial_placement_price)
                                           - 1) * 100 < (self.lo_allowable_slippage * -1):

                root.info("{} {} Limit Order Slippage has exceeded {}% in an unfavorable direction.\n"
                          "Canceling outstanding limit order.\n"
                          "Executing a Market Order.".format(self.id, side, self.lo_allowable_slippage))

                status = auth_client.cancel_order(key)
                if type(status) is dict:
                    if status['message'] == 'Order already done':
                        queue.enter(0, 1, self.gdax_limit_reprice)
                        return

                queue.enter(1, 1, self.gdax_limit_reprice)

                return

            elif side == "buy" and dec(order_update['price']) != dec(order_book_update['bids'][0][0]) \
                    or side == 'sell' and dec(order_update['price']) != dec(order_book_update['asks'][0][0]):

                self.lo_order_book = order_book_update
                root.info("{} Order book has shifted. Canceling and repricing order.".format(self.id))
                status = auth_client.cancel_order(key)
                if isinstance(status, dict):
                    if status['message'] == 'Order already done':
                        queue.enter(0, 1, self.gdax_limit_reprice)
                        return
                queue.enter(1, 1, self.gdax_limit_order, (side,))

                return

        if len(self.lo_fill_orders['open']) > 0:
            queue.enter(1, 1, self.gdax_limit_reprice)

        # If there are no open orders and the current order size has been filled declare success!
        elif len(self.lo_fill_orders['closed']) > 0 and len(self.lo_fill_orders['open']) == 0 and self.lo_current_fill == self.lo_current_order_size:
            order_completed()
        # If there are no open orders and the current order size has NOT been filled then WTF execute a market order STAT!
        elif len(self.lo_fill_orders['closed']) >= 0 and len(self.lo_fill_orders['open']) == 0 and self.lo_current_fill < self.lo_current_order_size:
            order_completed()

            if side == "buy":
                queue.enter(0, 1, self.gdax_buy_)
            else:
                queue.enter(0, 1, self.gdax_sell)

    def gdax_buy_(self):
        retry = 0
        dustless_quote_allocation = self.quote_allocation - (self.quote_allocation % self.quote_currency_spec.min_size)
        while retry < 5 and dustless_quote_allocation >= self.quote_currency_spec.min_size:
            attempts = 0
            dustless_quote_allocation = self.quote_allocation - (
                self.quote_allocation % self.quote_currency_spec.min_size)
            # Place the buy order with GDAX
            while attempts <= 10:
                try:
                    status = auth_client.buy(funds=str(dustless_quote_allocation), product_id=self.id, type='market')
                    retry += 1
                    if 'message' in status:
                        raise Exception(status)
                    break
                except Exception as e:
                    root.warning(e, status)
                    attempts += 1
                    time.sleep(2)
                    continue
                    # If the order fails, stop the next part for executing.
            else:
                if attempts >= 10:
                    break

            # Query GDAX for order status
            while status['settled'] == False:
                attempts = 0
                while attempts <= 10:
                    try:
                        status = auth_client.get_order(status['id'])
                        if 'message' in status:
                            raise Exception(status)
                        print("Trade status: Pending")
                        break
                    except Exception as e:

                        root.warning(e, status)
                        attempts += 1
                        time.sleep(2)
                        continue
                time.sleep(2)

            # If the order status returns a settle == True flag, but a executed value of 0, then the order failed.

            if decimal.Decimal(status['executed_value']) == 0 and status['settled'] == True:
                print("Retry: {}".format(retry))
                time.sleep(2)
                continue
            elif decimal.Decimal(status['executed_value']) > 0:

                trade_id = status['id']
                side = status['side']
                trade_time = status["done_at"]
                fees = decimal.Decimal(status['fill_fees'])
                filled_size = decimal.Decimal(status['filled_size'])
                executed_value = decimal.Decimal(status['executed_value'])
                settled = status['settled']
                price = round(executed_value / filled_size, 2)
                net = executed_value - fees

                self.buy_orders.append(status)

                print("Trade status: Confirmed")
                print(
                    "Bought {} {} @ {} {} For {} {}".format(filled_size, self.base_currency, price, self.quote_currency,
                                                            round(executed_value, 2), self.quote_currency))
                bookkeeper.base_buy_allocation_update(self, filled_size, executed_value, fees)
                bookkeeper.record_trade(self.id, side, filled_size, price, executed_value,
                                        fees, net, self.advice_detail, trade_id, self.base_allocation,
                                        self.quote_allocation, self.trade_track_file_path, self)
                fills = (auth_client.get_fills(status['id']))
                print("Fills:\n" + ("-" * 10))
                for list in fills:
                    for dict in list:
                        print("Trade ID: {} Size: {} Price: {}".format(dict['trade_id'], dict['size'],
                                                                       round(decimal.Decimal(dict['price']), 2)))

                break
            else:
                break

        else:
            if retry > 4:

                self.lo_attempt_tracker = 0
                self.lo_followup_counter = 0
                self.lo_initial_placement_price = 0
                self.lo_current_placement_price = 0
                self.lo_initial_order_size = 0
                self.lo_current_order_size = 0
                self.lo_time_tracker = 0
                self.lo_order_book = None
                self.lo_current_fill = 0
                self.lo_fill_orders = {"closed": {}, "open": {}}
                raise Exception("Could not place trade with GDAX")

    def gdax_sell(self):
        retry = 0
        dustless_base_allocation = self.base_allocation - (self.base_allocation % self.base_currency_spec.min_size)

        while retry < 5 and self.base_allocation >= self.base_min_size:
            dustless_base_allocation = self.base_allocation - (self.base_allocation % self.base_currency_spec.min_size)
            attempts = 0
            # Place the sell order with GDAX
            while attempts < 10:
                try:
                    status = auth_client.sell(size=str(dustless_base_allocation), product_id=self.id, type='market')
                    retry += 1
                    if "message" in status:
                        raise Exception(status)
                    break
                except Exception as e:
                    print("There was a problem placing a sell order with GDAX ({})".format(e))
                    print("Attempt {}".format(attempts))
                    attempts += 1
                    time.sleep(2)
                    continue

            # If the order fails, stop the next part for executing.
            else:
                if attempts >= 10:
                    break

            # Query GDAX for order status
            while status['settled'] == False:
                attempts = 0
                while attempts < 10:
                    try:
                        status = auth_client.get_order(status['id'])
                        if 'message' in status:
                            raise Exception(status)
                        break
                    except Exception as e:
                        print("There was a problem updating the order status")
                        print("Attempt {}".format(attempts))
                        attempts += 1
                        time.sleep(2)
                        continue

                print("Trade status: Pending")
                time.sleep(2)

            # unpack response
            trade_id = status['id']
            side = status['side']
            trade_time = status["done_at"]
            fees = decimal.Decimal(status['fill_fees'])
            filled_size = decimal.Decimal(status['filled_size'])
            executed_value = decimal.Decimal(status['executed_value'])
            specified_funds = executed_value + fees
            settled = status['settled']
            price = round(executed_value / filled_size, 2)
            net = executed_value - fees

            if executed_value == 0 and settled == True:
                print("Retry: {}".format(retry))
                time.sleep(2)
                continue
            elif executed_value > 0:
                self.sell_orders.append(status)

                print("Trade status: Confirmed")
                print("Sold {} {} @ {} {} For {} {}".format(filled_size, self.base_currency, price, self.quote_currency,
                                                            round(executed_value), 2), self.quote_currency)
                fills = (auth_client.get_fills(trade_id))
                print("Fills:\n" + ("-" * 10))
                for list in fills:
                    for dict in list:
                        print("Trade ID: {} Size: {} Price: {}".format(dict['trade_id'], dict['size'],
                                                                       round(decimal.Decimal(dict['price']), 2)))
                bookkeeper.base_sell_allocation_update(self, specified_funds, filled_size, fees)

                bookkeeper.record_trade(self.id, side, filled_size, price, executed_value, fees, net,
                                        self.advice_detail, trade_id, self.base_allocation, self.quote_allocation,
                                        self.trade_track_file_path, self)
                break

            else:
                break
        else:
            if retry > 4:
                self.lo_attempt_tracker = 0
                self.lo_followup_counter = 0
                self.lo_initial_placement_price = 0
                self.lo_current_placement_price = 0
                self.lo_initial_order_size = 0
                self.lo_current_order_size = 0
                self.lo_time_tracker = 0
                self.lo_order_book = None
                self.lo_current_fill = 0
                self.lo_fill_orders = {"closed": {}, "open": {}}
                raise Exception("Could not place trade with GDAX")

    def get_times(self):
        # This function gets the current epoch and rounds up or down to the nearest hour to grab pricing info.
        # 3600 is an hour in epoch. 36000 is 10 hours in epoch.  The endtime is the hour closest to the current
        # time where the measurement ends.  Start time is either 10 or 25 hours before end time of measurement
        # 9000 is 25 hours epoch.

        # When making determining start and end times, it is important to remember that the end candl you are requesting
        # runs up to the next hour.  Eg. A request with 4pm end time with a 60 minute candle covers 4-5pm.

        frequency = self.frequency * 60

        times = {}

        epoch = int(time.time())

        times["endhour_indicator"] = (frequency * ((epoch) // frequency)) - frequency - (self.lagtime * frequency)  #
        times["starthour_indicator"] = times["endhour_indicator"] - (self.indicator_hours * frequency)

        times["endhour_baseline"] = (frequency * ((epoch) // frequency)) - frequency - (self.lagtime * frequency)
        times["starthour_baseline"] = times["endhour_baseline"] - (self.baseline_hours * frequency)

        times["hour_over_end"] = (frequency * ((epoch) // frequency)) - frequency
        times['previous_hour'] = (frequency * ((epoch) // frequency)) - (frequency * 2)

        times["buy_down_start_hour"] = times["hour_over_end"] - (self.buy_down_trigger_hrs * frequency)

        times["sell_up_start_hour"] = times["hour_over_end"] - (self.sell_up_trigger_hrs * frequency)

        times["buy_up_start_hour"] = times["hour_over_end"] - (self.buy_up_trigger_hrs * frequency)

        times["sma_sell_change_hour"] = times["hour_over_end"] - (self.sma_sell_change_trigger_hours * frequency)

        times["sma_sell_constraint_hour"] = times["hour_over_end"] - (self.sma_sell_constraint_trigger_hours * frequency)

        # Note:  This is breaking from the structure. Collecting a single list of prices, which
        # I'll later use to construct a number of different SMAs by referencing this list.
        times["endhour_long_baseline"] = (frequency * ((epoch) // frequency)) - frequency - (self.lagtime * frequency)
        times["starthour_long_baseline"] = times["endhour_long_baseline"] - (self.baseline_long_hours * frequency)

        # Let's extract the start time(lowest epoch) and the end time(highest epoch) of the request to GDAX
        times["req_start"] = times[min(times.keys(), key=(lambda k: times[k]))]
        times["req_end"] = times[max(times.keys(), key=(lambda k: times[k]))]

        return times

    def candle_database_handler(self, start_time, end_time, candle_size):

        # delete un-needed previous candles from memory
        for index, row in enumerate(self.candles):
            if row[0] < start_time or row[0] > end_time:
                del self.candles[index]

        # Check memory for missing candles.  In the interests of time, I've also included code to group together
        # sequential numbers to make requesting easier later.  This should give us multiple sequential periods to
        # request with GDAX.

        missing_candles = []
        request_index = 0
        for time in range(start_time, end_time + candle_size, candle_size):
            candle_list = [candle[0] for candle in self.candles]
            if time not in candle_list:

                if len(missing_candles) > 0:
                    if time - candle_size == missing_candles[request_index][-1]:
                        missing_candles[request_index].append(time)

                    else:
                        request_index += 1

                        missing_candles.append([])
                        missing_candles[request_index].append(time)

                else:
                    missing_candles.append([])
                    missing_candles[request_index].append(time)

        missing_candles.sort()
        root.info("Algo candle requirements: {:.0f} {} minute candles. Range: {} UTC to {} UTC"
                  .format((end_time - start_time) / (self.frequency * 60) + 1, self.frequency,
                  datetime.datetime.utcfromtimestamp(start_time),
                  datetime.datetime.utcfromtimestamp(end_time)))
        root.info("{} candle(s) missing from memory".format(sum([len(list) for list in missing_candles])))

        return missing_candles

    def get_hist_price(self, missing_candles):

        request_size = 200
        product = self.id
        frequency = self.frequency
        candle_size = frequency * 60
        public_client = gdax.PublicClient()

        total_candles_to_update = sum([len(list) for list in missing_candles])
        candles_to_return = []
        for period in missing_candles:

            # Define start and end times for the period we are about to request
            start = period[0]
            end = period[-1] + (frequency * 60)

            # Define an empty list to put results into
            period_pend_data = []

            for epoch in range(start, end, candle_size * request_size):

                request_start = epoch
                request_end = epoch + (candle_size * request_size)
                retry = 0

                while retry < 3:
                    if request_end > end:
                        request_end = end
                    try:
                        time.sleep(1)
                        data = public_client.get_product_historic_rates(product_id=product,
                                                                        start=time.strftime('%Y-%m-%dT%H:%M:%SZ',
                                                                                            time.gmtime(request_start)),
                                                                        end=time.strftime('%Y-%m-%dT%H:%M:%SZ',
                                                                                          time.gmtime(request_end)),
                                                                        granularity=candle_size)
                        time.sleep(2)
                        if isinstance(data, list) == False or len(data) == 0:
                            raise Exception(data)

                        else:
                            period_pend_data.extend(data)
                            break


                    except Exception as e:
                        root.warning("Import Error: Range {} to {} Retry:{}".format(
                            datetime.datetime.utcfromtimestamp(request_start),
                            datetime.datetime.utcfromtimestamp(request_end), retry + 1))
                        root.debug(e)
                        retry += 1
                        time.sleep(3)


            period_pend_data.sort()


            epoch_to_update = [candle for candle in period]
            period_pend_epoch_list = [candle[0] for candle in period_pend_data]

            # Deduplicate period_pend_data
            b = []
            [b.append(candle) for candle in period_pend_data if candle not in b]
            period_pend_data = b

            # Delete candles that fall outside the range we need. ie extra candles returned from GDAX.
            period_pend_data = [candle for candle in period_pend_data if candle[0] in period and candle]

            # Delete epochs from self.missing_candles that have been retrieved.

            if len(self.missing_candles) > 0:
                delete_index = [index for index, epoch in enumerate(self.missing_candles) if epoch in period_pend_epoch_list]
                delete_index.reverse()
                for index in delete_index:
                    del self.missing_candles[index]

            # Add new missing candles to to self.missing_candles

            missing = [epoch for epoch in epoch_to_update if epoch not in period_pend_epoch_list]
            for epoch in missing:
                if epoch in self.missing_candles:
                    root.info(
                        "Still unable to retrieve data for {} UTC".format(datetime.datetime.utcfromtimestamp(epoch)))

                else:

                    root.info("Could not retrieve data for {} UTC".format(datetime.datetime.utcfromtimestamp(epoch)))
                    self.missing_candles.append(epoch)

            try:
                root.info("Successfully fetched {} records ranging {} UTC to {} UTC".format(len(period_pend_data),
                                                                                    datetime.datetime.utcfromtimestamp(
                                                                                        period_pend_data[0][0]),
                                                                                    datetime.datetime.utcfromtimestamp(
                                                                                        period_pend_data[-1][0])))
            except IndexError:
                root.info("No candles were returned from GDAX for period: {} to {}.".format(
                    datetime.datetime.utcfromtimestamp(period[0]), datetime.datetime.utcfromtimestamp(period[-1])))

            candles_to_return.extend(period_pend_data)


        return candles_to_return

    def analysis(self):
        try:
            print("\n{}\n Advice: {} {}\n{}".format("-" * 40, self.id,
                                                    time.strftime("%m-%d-%y %I:%M %p %Z",
                                                                  time.localtime(time.time())), "-" * 40))

            cmv = get_cmv(self.id)

            times = self.get_times()

            missing_candles = self.candle_database_handler(times["req_start"], times["req_end"], self.frequency * 60)

            histdata = self.get_hist_price(missing_candles)

            self.candles.extend(histdata)

            his_pric_data = extract_pricing_data(self.candles, times, self.id, detail, self.indicator_hours,
                                                 self.baseline_hours,
                                                 self.buy_down_trigger_hrs, self.sell_up_trigger_hrs,
                                                 self.buy_up_trigger_hrs,
                                                 self.sma_sell_change_trigger_hours,
                                                 self.sma_sell_constraint_trigger_hours)

            sma = compute_sma(his_pric_data, self.baseline_long_hours, self.indicator_long_hours,
                              self.sma_indicator_V3,
                              self.sma_baseline_V3)  # note: his_pric_data is a tuple

            advice(sma, self.id, detail, self, cmv, self.buy_threshold, self.sell_threshold,
                   self.buy_down_trigger, self.sell_down_trigger,
                   self.sell_up_trigger, self.buy_up_trigger, self.sma_sell_change_threshold,
                   self.sell_threshold_adjust,
                   self.sma_sell_constraint, self.sell_up_trigger_stop, self.sell_up_trigger2,
                   self.sell_up_trigger_stop2,
                   self.sma_buy_change_threshold, self.buy_threshold_adjust, self.buy_down_last_trade,
                   self.buy_down_low_profit,
                   self.sell_up_after_trade_time, self.sell_up_after_trade_profit,
                   self.sell_up_after_trade_adjust,
                   self.abandon_sell_time, self.abandon_sell_trigger, self.abandon_sell_adjust,
                   self.sma_threshold_down,
                   self.buy_down_trigger_adjusted, self.sma_sell_constraint2, self.buy_down_release1,
                   self.buy_down_release2,
                   self.buy_down_sell_constraint, self.sell_up_advice_time, self.sell_up_advice_change,
                   self.sma_buy_constraint,
                   self.bear_market_on_switch, self.bear_threshold, self.buy_threshold_V3,
                   self.sell_threshold_V3, self.bear_profit, self.bear_sell_time, self.variance_off, self)
            
            queue.enterabs((time.time() // (trading_pair_collector[tradingpair].frequency * 60)) *
                           (self.frequency * 60) + self.frequency * 60, 1, self.analysis)


        except Exception as e:
            root.debug(traceback.print_exc())
            root.warning("There was an exception, restarting loop: {}". format(e))
            queue.enterabs(time.time() + 30, 1, self.analysis)


class Accounts():
    def __init__(self, account):
        try:
            self.id = account['id']
            self.currency = account["currency"]
            self.balance = decimal.Decimal(account["balance"])
            self.available = decimal.Decimal(account["available"])
            self.hold = decimal.Decimal(account["hold"])
            self.to_allocate = decimal.Decimal(self.available)

        except KeyError:
            raise

    def subtract_allocation(self, allocation_amount):

        if allocation_amount > self.to_allocate:
            raise Exception("Over allocated")
        else:
            self.to_allocate -= allocation_amount

    def update_accounts(self):
        auth_client.get_account(self.id)


class Currency_Specs():
    def __init__(self, currencies):
        self.id = currencies['id']
        self.name = currencies['name']
        self.min_size = decimal.Decimal(currencies['min_size'])
        self.status = currencies['status']
        self.message = currencies['message']


# set up logger

kwargs = {"DEBUG": 50, "INFO": 20, "WARNING": 30, "ERROR": 40, "CRITICAL": 50}
log_print_level = menu_structure("Pick a logging output level.  All messages at level or higher are printed."
                                 "  Recommended is INFO or above:", *kwargs)
# set up format for print and file logs
formatter = logging.Formatter('%(asctime)s ; %(levelname)s ; %(message)s')

# console handler
root = logging.getLogger()
root.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(log_print_level)
console_handler.setFormatter(formatter)
root.addHandler(console_handler)

# file handler
log_filename = 'logs/bot_log.out'
file_handler = logging.handlers.RotatingFileHandler(log_filename, maxBytes=10000000, backupCount=10)
file_handler.setFormatter(formatter)
root.addHandler(file_handler)

if __name__ == "__main__":

    # set up task handler
    queue = sched.scheduler(time.time, time.sleep)

    # Set up a dictionary with class objects, each one being an account pulled from GDAX
    account_collector = {}

    for tradingpair in getaccounts():
        new_account = Accounts(tradingpair)
        account_collector[new_account.currency] = Accounts(tradingpair)

    currency_spec_dict = {}
    for currency in auth_client.get_currencies():
        currency_spec_dict[currency['id']] = Currency_Specs(currency)

    # Set up a dictionary with class objects, each one being a trading pair set up by the user.
    trading_pair_collector = {}

    while len(trading_pair_collector) == 0 or answer == 'yes':
        product_holder = get_products()
        if product_holder["id"] in trading_pair_collector:
            print("You have already configured this product")
        else:
            new_wallet = trading_pair(product_holder)
        product = new_wallet.id
        trading_pair_collector[product] = new_wallet

        answer = menu_structure("Would you like to configure another product for trading?", "yes", "no")

    if len(trading_pair_collector) == 0:
        root.critical("You have no configured trading pairs. Exiting...")
        exit(1)

    detail = detail_level()

    print("\n Alright son. Bot is locked and loaded.")

    for tradingpair in trading_pair_collector:

        queue.enterabs((time.time() // (trading_pair_collector[tradingpair].frequency * 60))
                        * (trading_pair_collector[tradingpair].frequency * 60) + \
                        trading_pair_collector[tradingpair].frequency * 60, 1, trading_pair_collector[tradingpair].analysis)
 
    while True:

        # start/restart the queue on each loop
        queue.run()

        time.sleep(.5)