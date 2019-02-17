
import os
import glob
import json
import re

from Acquire.Service import get_service_account_bucket, get_service_info
from Acquire.Accounting import Account, Transaction, TransactionInfo, Ledger
from Acquire.ObjectStore import string_to_date, string_to_datetime, \
                                string_to_decimal

from Acquire.Accounting._account import _get_date_from_key, \
                                        _get_datetime_from_key, \
                                        _sum_transactions

test_dir = "/private/var/folders/hw/snr3wkg97sjf6cmv12jgj0040000gq/T/pytest-of-chris/pytest-255/objstore0/testing_objstore"

bucket = get_service_account_bucket(test_dir)

accounts_data = glob.glob("%s/accounting/accounts/*._data" % test_dir)

accounts = {}

for account_data in accounts_data:
    line = open(account_data,"r").read()
    account = Account.from_data(json.loads(line))
    print("Reading account '%s'" % account)

    account_root = account_data.replace("._data", "")
    balances_data = glob.glob("%s/balance/*" % account_root)

    balances = {}
    print("    Loading balances...")

    for balance_data in balances_data:
        date = _get_date_from_key(balance_data)
        line = open(balance_data, "r").read()
        balance = json.loads(line)
        balances[date] = balance

    transactions_data = glob.glob("%s/*/*/*._data" % account_root)
    transactions = {}

    print("    Loading transactions...")
    for transaction_data in transactions_data:
        datetime = _get_datetime_from_key(transaction_data)
        transaction_info = TransactionInfo(
                                transaction_data.replace("._data", ""))
        transactions[datetime] = transaction_info

    accounts[account.uid()] = {"account": account,
                               "balances": balances,
                               "transactions": transactions}


def verify_balances(account, balances, transactions):
    days = list(balances.keys())
    days.sort()

    times = list(transactions.keys())
    times.sort()

    i = 0
    ending_balance = None

    typs = ["balance", "liability", "receivable"]

    total_balance = {}

    for typ in typs:
        total_balance[typ] = 0

    failures = []

    for day in days:
        starting_balance = balances[day]

        b = {}
        for typ in typs:
            b[typ] = string_to_decimal(starting_balance[typ])

        starting_balance = b

        if ending_balance is not None:
            if starting_balance != ending_balance:
                for typ in typs:
                    a = starting_balance[typ]
                    b = ending_balance[typ]
                    c = last_balance[typ]
                    if a != b:
                        failures.append((day,a,b,c))
                        print("FAILED (%s - %s): %s | %s | %s" % (day, typ, a, b, c))

                for t in last_transactions:
                    print(t, end=" ")
                print("")

        day_keys = []

        while True:
            if i >= len(times):
                break

            time = times[i]
            if time.date() > day.date():
                break

            day_keys.append(transactions[time])
            i += 1

        if len(day_keys) > 1:
            print("MULTI-PER-DAY %s" % day)

        day_sum = _sum_transactions(day_keys)

        d = {}
        d["balance"] = day_sum[0]
        d["liability"] = day_sum[1]
        d["receivable"] = day_sum[2]

        ending_balance = {}

        for typ in typs:
            total_balance[typ] += d[typ]
            ending_balance[typ] = starting_balance[typ] + d[typ]

        last_balance = starting_balance
        last_transactions = day_keys

    summed_balance = _sum_transactions(transactions.values())

    if total_balance != ending_balance:
        print("FAILED: %s versus %s" % (total_balance, ending_balance))
        print("SUMMED: %s" % str(summed_balance))

    return failures


for uid in accounts.keys():
    account = accounts[uid]["account"]
    print("\nVerifying account %s" % account)

    failures = verify_balances(account, accounts[uid]["balances"],
                               accounts[uid]["transactions"])

    accounts[uid]["failures"] = failures
