
import traceback
import decimal
import datetime
import pandas
import logging

log = logging.getLogger(__name__)


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
        print(e,":",c)
    while True:
        try:
            choice = choices[int(input('Enter a choice:'))]
            print(choice)
            break
        except Exception:
            print('Invalid Entry. Try again.')
    return choice

def quote_allocation_set(instance):
    while True:
        try:
            allocation = input(
                "{} Account Balance: {} \n{} Available to Allocate: {} \nMinimum to Allocate : {} \nAllocate an amount to trade with *OR press enter"
                " to allocate ALL AVAILABLE :".format(
                    instance.quote_account.currency, format(instance.quote_account.balance, ".8f"),
                    instance.quote_account.currency, format(instance.quote_account.to_allocate, ".8f"),
                    instance.quote_increment))

            if allocation == "":
                if (instance.quote_account.to_allocate) < instance.quote_increment:
                    allocation = 0
                else:
                    allocation = instance.quote_account.to_allocate

            if decimal.Decimal(allocation) < 0:
                raise Exception("Must be a positive number")

            if decimal.Decimal(allocation) < instance.quote_increment and decimal.Decimal(allocation) > 0:
                print("Minimum allocation is {} {}. Please try again.".format(instance.quote_increment,
                                                                              instance.quote_currency))
                continue

            instance.quote_account.subtract_allocation(decimal.Decimal(allocation))
            print(allocation)
            return decimal.Decimal(allocation)

        except ValueError:
            print("You must enter a number")
            continue

        except Exception as e:
            print("Error try again:", e, traceback.print_exc())


def base_allocation_set(instance):
    while True:
        try:
            allocation = input(
                "\n{} Account Balance: {} \n{} Available to Allocate: {} \nMinimum to Allocate: {} \nAllocate an amount to trade with"
                " *OR* Press enter to allocate ALL AVAILABLE.".format(
                    instance.base_account.currency, format(instance.base_account.balance, '.8f'),
                    instance.base_account.currency, format(instance.base_account.to_allocate, '.8f'),
                    instance.base_min_size))
            if allocation == "":
                if instance.base_account.to_allocate < instance.base_min_size:
                    allocation = 0
                else:
                    allocation = instance.base_account.to_allocate

            if decimal.Decimal(allocation) < 0:
                raise Exception("Must be a positive number")

            if decimal.Decimal(allocation) < instance.base_min_size and decimal.Decimal(allocation) > 0:
                print(
                    "Minimum allocation is {} {}. Please try again.".format(instance.base_min_size,
                                                                            instance.base_currency))
                continue

            instance.base_account.subtract_allocation(decimal.Decimal(allocation))
            print(allocation)
            return decimal.Decimal(allocation)
        except ValueError:
            print("You must enter a number")
            continue
        except Exception as e:
            print("ERROR try again:", e, traceback.print_exc())


def reload_allocations(instance):

    try:
        with open(instance.trade_track_file_path) as file:
            df = pandas.read_csv(file, float_precision="high")
        quote_allocation = decimal.Decimal(str(df.at[0,"quote_alloc"]))
        base_allocation = decimal.Decimal(str(df.at[0,"base_alloc"]))

        if quote_allocation < instance.quote_increment:
            instance.quote_allocation = decimal.Decimal(0)

        if base_allocation < instance.base_min_size:
            instance.base_allocation = decimal.Decimal(0)



        reload_decision = menu_structure("Previous allocations of {} {} and {} {} found.  Would you like to reload them?".format(
                    round(float(quote_allocation),2), instance.quote_currency, round(float(base_allocation),8),
                    instance.base_currency), "Yes", "No")

        # Add debug logging to address Chris's reload issues
        log.debug("Blotter Quote {}, Blotter Base {}".format(quote_allocation, base_allocation))
        log.debug("Coinbase Quote {}, Coinbase Base {}".format(instance.quote_account.balance,
                                                               instance.base_account.balance))
        log.debug("Quote remaming {}, Base Remaining {}". format(instance.quote_account.to_allocate,
                                                                 instance.base_account.to_allocate))

        if reload_decision == "No":

                instance.quote_allocation = quote_allocation_set(instance)
                instance.base_allocation = base_allocation_set(instance)
        else:
            if instance.quote_account.to_allocate < quote_allocation or instance.base_account.to_allocate < base_allocation:
                raise Exception(
                    "There is a discrepancy between your account balance and the trade register.  Please reallocate funds.")


            instance.quote_allocation = quote_allocation
            instance.quote_account.subtract_allocation(decimal.Decimal(instance.quote_allocation))

            instance.base_allocation = base_allocation
            instance.base_account.subtract_allocation(decimal.Decimal(instance.base_allocation))

        if instance.base_allocation != base_allocation or instance.quote_allocation != quote_allocation:
            record_allocation_adjustment(instance)

    except FileNotFoundError:
        print("Could not find previous allocations.")
        instance.quote_allocation = quote_allocation_set(instance)
        instance.base_allocation = base_allocation_set(instance)
        record_allocation_adjustment(instance)
    except Exception as error:
        print("Something went wrong.", error, traceback.print_exc())
        instance.quote_allocation = quote_allocation_set(instance)
        instance.base_allocation = base_allocation_set(instance)
        record_allocation_adjustment(instance)





def record_allocation_adjustment(instance):
    time = datetime.datetime.utcnow().isoformat()
    ids = instance.id
    side = "REALLOC"
    size = "*"
    price = "*"
    gross = "*"
    fees = "*"
    net = "*"
    advice = "*"
    trade_id = "*"
    write_data = [time, ids, side, size, price, gross, fees, net, advice, trade_id, instance.base_allocation,
                  instance.quote_allocation]
    header = ["time", "id", "side", "size", "price", "gross", "fees", "net", "advice", "trade_id", "base_alloc",
              "quote_alloc"]

    try:
        with open(instance.trade_track_file_path) as file:
            df = pandas.read_csv(file, index_col=0)
        df.loc[-1] = write_data
        df.index = df.index + 1
        df = df.sort_index()
        df.to_csv(instance.trade_track_file_path)
        logging.info("Allocaiton adjustment successfully recorded to {} trade register.".format(instance.id))

    except FileNotFoundError:
        log.info("Existing {} trade register not found.  Creating a new register.".format(instance.id))
        df = pandas.DataFrame(columns = header)
        df.loc[-1] = write_data
        df.index = df.index + 1
        df = df.sort_index()
        df.to_csv(instance.trade_track_file_path, mode='w+')



    except Exception as e:
        print(e, traceback.print_exc())

def record_trade(id, side, size, price, gross, fees, net, advice, trade_id, base_alloc, quote_alloc, file, instance):
    time = datetime.datetime.utcnow().isoformat()
    write_data = [time, id, side, size, price, gross, fees, net, advice, trade_id, base_alloc, quote_alloc]
    header = ["time", "id", "side", "size", "price", "gross", "fees", "net", "advice", "trade_id", "base_alloc", "quote_alloc"]
    pend_data = []

    try:
        with open(file) as filename:
            df = pandas.read_csv(filename, index_col=0)
        df.loc[-1] = write_data
        df.index = df.index + 1
        df = df.sort_index()
        df.to_csv(file)
        log.info("Trade recorded successfully to {} trade register.".format(id))

        # Reset counters
        instance.lo_attempt_tracker = 0
        instance.lo_followup_counter = 0
        instance.lo_initial_placement_price = 0
        instance.lo_current_placement_price = 0
        instance.lo_initial_order_size = 0
        instance.lo_current_order_size = 0
        instance.lo_time_tracker = 0
        instance.lo_order_book = None
        instance.lo_current_fill = 0
        instance.lo_fill_orders = {"closed":{}, "open": {}}


    except FileNotFoundError:
        log.info("Existing {} trade register not found.  Creating a new register.".format(id))
        df = pandas.DataFrame(columns=header)
        df.loc[-1] = write_data
        df.index = df.index + 1
        df = df.sort_index()
        df.to_csv(file, mode='w+')

    except Exception as e:
        log.warning("Bookkeeper:record_trade malfunction!: {}".format(e))

def base_buy_allocation_update(instance, bought, sold, fees):
    instance.base_allocation += bought
    instance.quote_allocation -= (sold + fees)
    log.info("Allocation updated: +{:0.7f} {}  -{:0.2f} {}".format(bought, instance.base_currency, sold - fees, instance.quote_currency))


def base_sell_allocation_update(instance, bought, sold, fees):
    instance.base_allocation -= sold
    instance.quote_allocation += (bought - fees)
    log.info("Allocation updated: +{:0.2f} {} -{:0.7f} {}".format(bought - fees, instance.quote_currency, sold , instance.base_currency))







