import datetime
import tzlocal
import pytz
import json
import zlib
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
# TODO:
# - ability to scale up / down the resolution of a TypicalWeek object without information loss
# - ability to generate a TypicalWeek instance from Union / Intersection of two TypicalWeek instances.


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


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

    @property
    def bitmap_as_hex(self):
        return str(hex(int(''.join(map(str, self.bitmap)), 2)))[:-1]

    def __eq__(self, other):
        my_hex = self.bitmap_as_hex
        other_hex = other.bitmap_as_hex
        return (
            my_hex == other_hex
            and self._tzinfo.zone == other._tzinfo.zone
            and self.resolution_in_minutes == other.resolution_in_minutes)

    def __add__(self, other):
        if self.resolution_in_minutes <= other.resolution_in_minutes:
            assert other.resolution_in_minutes % self.resolution_in_minutes == 0
            assert other.tzinfo == self.tzinfo
            scaled_other = other.copy(self.resolution_in_minutes)
            bitmap_as_hex = str(hex(int(self.bitmap_as_hex, 16) & int(scaled_other.bitmap_as_hex, 16)))[:-1]
            tw = TypicalWeek(
                resolution_in_minutes=scaled_other.resolution_in_minutes,
                timezone=self._tzinfo.zone,
                tz_aware=self.tz_aware,
                bitmap_as_hex=bitmap_as_hex)
            return tw

        else:
            return other.__add__(self)

    def __mul__(self, other):
        if self.resolution_in_minutes <= other.resolution_in_minutes:
            assert other.resolution_in_minutes % self.resolution_in_minutes == 0
            assert other.tzinfo == self.tzinfo
            scaled_other = other.copy(self.resolution_in_minutes)
            bitmap_as_hex = str(hex(int(self.bitmap_as_hex, 16) | int(scaled_other.bitmap_as_hex, 16)))[:-1]
            tw = TypicalWeek(
                resolution_in_minutes=scaled_other.resolution_in_minutes,
                timezone=self._tzinfo.zone,
                tz_aware=self.tz_aware,
                bitmap_as_hex=bitmap_as_hex)
            return tw

        else:
            return other.__add__(self)

    def copy(self, resolution_in_minutes=None, lossy=False):
        if resolution_in_minutes is None:
            resolution_in_minutes = self.resolution_in_minutes
        assert MINUTES_IN_A_DAY % resolution_in_minutes == 0
        if resolution_in_minutes < self.resolution_in_minutes:
            assert self.resolution_in_minutes % resolution_in_minutes == 0
            change_factor = self.resolution_in_minutes / resolution_in_minutes
            bitmap = []
            for bit in self.bitmap:
                bitmap.extend([bit] * change_factor)
        elif resolution_in_minutes > self.resolution_in_minutes:
            assert resolution_in_minutes % self.resolution_in_minutes == 0
            change_factor = resolution_in_minutes / self.resolution_in_minutes
            bitmap = []
            for chunk in chunks(self.bitmap, change_factor):
                if lossy:
                    bit = any(chunk)
                else:
                    bit = all(chunk)
                    if not bit:
                        if not any(chunk):
                            bit = False
                        else:
                            raise ValueError('Cannot garantee lossless resoltion change')
                bitmap.append(int(bit))
        else:
            bitmap = self.bitmap
        t = TypicalWeek(
            resolution_in_minutes=resolution_in_minutes,
            timezone=self._tzinfo.zone,
            tz_aware=self.tz_aware)
        t.bitmap = bitmap
        return t

    def dumps(self):
        json_str = json.dumps({
            'resolution_in_minutes': self.resolution_in_minutes,
            'bitmap_as_hex': self.bitmap_as_hex,
            'timezone': self._tzinfo.zone,
            'tz_aware': self.tz_aware
        })
        print(json_str)
        return zlib.compress(json_str)

    @classmethod
    def loads(cls, str_repr):
        params = json.loads(zlib.decompress(str_repr))
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

    def add_busy_interval(self, start_time, end_time):
        start_index, end_index = self._index_interval_from_datetime(start_time, end_time)
        for i in range(start_index, end_index):
            if not self._is_busy(i):
                self._set(i)

    def remove_busy_interval(self, start_time, end_time):
        start_index, end_index = self._index_interval_from_datetime(start_time, end_time)
        for i in range(start_index, end_index + 1):
            if self._is_busy(i):
                self._unset(i)

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
        for i in range(start_index, end_index):
            if self._is_busy(i) == busy:
                if current_interval_start_index is None:
                    current_interval_start_index = i
            else:
                if current_interval_start_index is not None:
                    interval = [int(current_interval_start_index), i - 1]
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
            # busy case
            _start_index = interval[0]
            _end_index = interval[1] + 1
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
            # raise warning that your timestamp is considered local
            t = t.replace(tzinfo=self.tzinfo)
        return t
