import datetime
import tzlocal
import pytz
import json
MINUTES_IN_A_DAY = 1440
MINUTES_IN_A_WEEK = 7 * MINUTES_IN_A_DAY
RESOLUTION_IN_MINUTES = 60

week = [1 for i in xrange(MINUTES_IN_A_WEEK / RESOLUTION_IN_MINUTES)]

# I want to be able to get intersection from bitmap
# I want to get a list of intervals from a bitmap
# I want to get a the list of intervals between two datetimes that
#   1) have the same resoltion as the bitmap
#   2) are between start_time and end_time
# I want to be able to create a bitmap from a list of intervals, a resolution in minutes and a number of days.
# ALL bitmapS ARE 7 DAYS LONG FOR A TYPICAL WEEK


class TypicalWeek(object):
    def __init__(self, resolution_in_minutes=60, timezone=None, tz_aware=False, bitmap_as_hex=None):
        assert MINUTES_IN_A_DAY % resolution_in_minutes == 0
        self.tz_aware = tz_aware
        if bitmap_as_hex is None:
            self.bitmap = [1 for i in xrange(MINUTES_IN_A_WEEK / resolution_in_minutes)]
        else:
            self.bitmap = map(int, list('{0:b}'.format(int(bitmap_as_hex, 16))))
        self.resolution_in_minutes = resolution_in_minutes
        if timezone is None:
            self._tzinfo = tzlocal.get_localzone()
        else:
            self._tzinfo = pytz.timezone(timezone)

    @property
    def tzinfo(self):
        if self.tz_aware:
            return self._tzinfo

    def dumps(self):
        json_str = json.dumps({
            'resolution_in_minutes': self.resolution_in_minutes,
            'bitmap_as_hex': str(hex(int(''.join(map(str, typical_week.bitmap)), 2)))[:-1],
            'timezone': self._tzinfo.zone,
            'tz_aware': self.tz_aware
        })
        print json_str
        return json_str

    @classmethod
    def loads(cls, str_repr):
        params = json.loads(str_repr)
        return cls(**params)

    def is_available(self, t):
        i = self._get_index_from_datetime(t)
        return not self._is_busy(i)

    def is_busy(self, t):
        i = self._get_index_from_datetime(t)
        return self._is_busy(i)

    def get_busy_intervals(self, start_time, end_time):
        return self._get_time_intervals(start_time, end_time, busy=True)

    def get_available_intervals(self, start_time, end_time):
        return self._get_time_intervals(start_time, end_time, busy=False)

    def add_event(self, start_time, end_time):
        print('add_event', start_time, end_time)
        start_index, end_index = self._index_interval_from_datetime(start_time, end_time)
        for i in range(start_index, end_index + 1):
            if not self._is_busy(i):
                self._set(i)
            else:
                raise ValueError()

    def get_time_interval(self, t):
        i = self._get_index_from_datetime(t)
        return (self._get_datetime_from_index(t, i), self._get_datetime_from_index(t, i + 1))

    def _is_busy(self, i):
        return self.bitmap[i % len(self.bitmap)] == 0

    def _set(self, i):
        self.bitmap[i % len(self.bitmap)] = 0

    def _unset(self, i):
        self.bitmap[i % len(self.bitmap)] = 1

    def _index_interval_from_datetime(self, start_time, end_time):
        assert end_time > start_time
        start_time = self._parse_datetime(start_time)
        end_time = self._parse_datetime(end_time)
        week_difference = end_time.isocalendar()[1] - start_time.isocalendar()[1]
        start_index = self._get_index_from_datetime(start_time)
        end_index = self._get_index_from_datetime(end_time) + len(self.bitmap) * week_difference
        return (start_index, end_index)

    def _get_time_intervals(self, start_time, end_time, busy=True):
        start_time = self._parse_datetime(start_time)
        end_time = self._parse_datetime(end_time)
        start_index, end_index = self._index_interval_from_datetime(start_time, end_time)
        intervals = []
        current_interval_start_index = None
        # if not busy:
        #     start_index -= 1
        for i in range(start_index, end_index):
            if self._is_busy(i) == busy:
                if current_interval_start_index is None:
                    current_interval_start_index = i
            else:
                if current_interval_start_index is not None:
                    interval = [current_interval_start_index, i - 1]
                    intervals.append(interval)
                    current_interval_start_index = None
        if current_interval_start_index is not None:
            index = end_index
            if busy:
                index += 1
            interval = [current_interval_start_index, index]
            intervals.append(interval)

        ref = start_time
        time_intervals = []

        for interval in intervals:
            _start_index = interval[0] if busy else interval[0] - 1
            _end_index = interval[1] if busy else interval[1] + 1
            interval_start_time = self._get_datetime_from_index(ref, _start_index)
            interval_end_time = self._get_datetime_from_index(ref, _end_index)
            ref = interval_end_time
            time_intervals.append([max(start_time, interval_start_time), min(interval_end_time, end_time)])
        return time_intervals

    def _get_index_from_datetime(self, t):
        t = self._parse_datetime(t)
        midnight = datetime.datetime(year=t.year, month=t.month, day=t.day, tzinfo=self.tzinfo)
        minutes = (t - midnight).seconds / (60 * self.resolution_in_minutes)
        index = t.weekday() * (MINUTES_IN_A_DAY / self.resolution_in_minutes) + minutes
        return index % len(self.bitmap)

    def _get_datetime_from_index(self, t, i):
        t = self._parse_datetime(t)
        dt = datetime.datetime(year=t.year, month=t.month, day=t.day)
        dt -= datetime.timedelta(days=t.weekday())
        dt += datetime.timedelta(minutes=i * self.resolution_in_minutes)
        return dt.replace(tzinfo=self.tzinfo)

    def _parse_datetime(self, t):
        if t.tzinfo is not None:
            if not self.tz_aware:
                raise ValueError('Only datetimes without timezone are allowed')
            t = t.astimezone(self.tzinfo).replace(tzinfo=self.tzinfo)
        else:
            t = t.replace(tzinfo=self.tzinfo)
        return t


typical_week = TypicalWeek(resolution_in_minutes=60)
now = datetime.datetime(2018, 9, 28, 11, 36, 30, 0)
monday = datetime.datetime(year=now.year, month=now.month, day=now.day) - datetime.timedelta(days=now.weekday())
for i in xrange(5):
    d = monday + datetime.timedelta(days=i)
    typical_week.add_event(d + datetime.timedelta(hours=9), d + datetime.timedelta(hours=12))
    typical_week.add_event(d + datetime.timedelta(hours=14), d + datetime.timedelta(hours=18))
current_index = typical_week._get_index_from_datetime(now)

print(now, typical_week.is_busy(now))
print('current interval', typical_week.get_time_interval(now))
print('busy', typical_week.get_busy_intervals(now, now + datetime.timedelta(days=1)))
print('busy', typical_week.get_busy_intervals(now, now + datetime.timedelta(hours=4)))
print('available', typical_week.get_available_intervals(now, now + datetime.timedelta(days=1)))
print('available', typical_week.get_available_intervals(now, now + datetime.timedelta(hours=4)))

str_repr = typical_week.dumps()
assert str_repr == TypicalWeek.loads(str_repr).dumps()