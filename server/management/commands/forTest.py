from datetime import datetime

date_str = '09-19-2022'

date_object = datetime.strptime(date_str, '%m-%d-%Y').date()
print(type(datetime(2023, 4, 7).date()))
print(type(date_object))
print(date_object)  # printed in default format

# parse [all - (1 "all")] [all, (начало семака, конец семака)]
# parse [all] [all - (today, today)]
# parse [1 1 date]
