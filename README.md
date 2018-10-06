
# WeeklyCalendar

A simple library to deal with weekly opening hours and other recurrent weekly events

## Usage
Methods will either return a Boolean or datetime based intervals.
```python
from weekly_calendar import WeeklyCalendar
from datetime import datetime, timedelta

now = datetime.now()
typical_week = WeeklyCalendar(resolution_in_minutes=60)
# typical_week is mapped into a bitmap with a bit representing one hour
assert typical_week.is_idle(now)
typical_week.add_busy_interval(now, now + timedelta(hours=3))
# the date doens't really matter, only the day of the week does
assert typical_week.is_busy(now)
busy_intervals = typical_week.get_busy_intervals(now, now + timedelta(hours=5))
# The result is a list of intervals (start_time, end_time)
idle_intervals = typical_week.get_idle_intervals(now, now + timedelta(hours=5))
# The result is a list of intervals (start_time, end_time)
```

You can also do union and intersection of different `WeeklyCalendar` objects:

```python
from weekly_calendar import WeeklyCalendar

tw_60 = WeeklyCalendar(resolution_in_minutes=60)
tw_30 = WeeklyCalendar(resolution_in_minutes=30)
# resulting objects will have the lowest resolution
tw_union = tw_30 + tw_60
tw_intersection = tw_30 * tw_60
```
You can change resolution of an existing `WeeklyCalendar` object:
```python
from weekly_calendar import WeeklyCalendar

tw_60 = WeeklyCalendar(resolution_in_minutes=60)
tw_60_to_30 = tw_60.copy(resolution_in_minutes=30)
```
Your `WeeklyCalendar` object is serializable:
```python
tw = WeeklyCalendar()
str_repr = tw.dumps()
tw_loaded = WeeklyCalendar.loads(str_repr)
# checks equal resolution, bitmap, and extra parameters
assert tw == tw_loaded
```
