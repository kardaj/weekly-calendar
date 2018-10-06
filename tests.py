from weekly_calendar import WeeklyCalendar
import datetime

start_time = datetime.datetime(2018, 9, 28, 9)
end_time = datetime.datetime(2018, 9, 28, 12)


def work_hour_typical_week(resolution_in_minutes):
    typical_week = WeeklyCalendar(resolution_in_minutes=resolution_in_minutes)
    now = datetime.datetime(2018, 9, 28, 11, 36, 30, 0)
    monday = datetime.datetime(year=now.year, month=now.month, day=now.day) - datetime.timedelta(days=now.weekday())
    for i in xrange(5):
        d = monday + datetime.timedelta(days=i)
        typical_week.add_busy_interval(d + datetime.timedelta(hours=9), d + datetime.timedelta(hours=12))
        typical_week.add_busy_interval(d + datetime.timedelta(hours=14), d + datetime.timedelta(hours=18))
    return typical_week


def test_add_busy_interval():

    def test_case(resolution):
        t = work_hour_typical_week(resolution)
        busy_interval = t.get_busy_intervals(start_time, end_time)[0]
        assert t.is_busy(start_time)
        assert not t.is_busy(end_time)
        assert busy_interval[0] == start_time
        assert busy_interval[1] == end_time
        assert t.get_closest_busy(end_time) > end_time
        assert t.get_closest_busy(start_time) == start_time
        assert t.get_closest_idle(start_time) == end_time

    for r in [120, 60, 30, 20, 15, 10, 5, 1]:
        test_case(r)


def extract_monday(tw):
    return ''.join(map(str, tw.bitmap[:len(tw.bitmap) / 7]))


def test_rescaling():
    tw_5 = work_hour_typical_week(5)
    tw_30 = work_hour_typical_week(30)
    tw_60 = work_hour_typical_week(60)
    tw_120 = work_hour_typical_week(120)

    tw_60_to_5 = tw_60.copy(resolution_in_minutes=5)
    tw_60_to_30 = tw_60.copy(resolution_in_minutes=30)
    tw_120_to_60 = tw_120.copy(resolution_in_minutes=60)
    tw_5_to_60 = tw_5.copy(resolution_in_minutes=60)

    assert extract_monday(tw_60_to_30) == extract_monday(tw_30)
    assert not extract_monday(tw_60_to_30) == extract_monday(tw_60)
    assert extract_monday(tw_60_to_5) == extract_monday(tw_5)
    assert extract_monday(tw_5_to_60) == extract_monday(tw_60)


def test_internals():
    monday_at_8 = datetime.datetime(2018, 9, 24, 8)
    monday_at_9 = datetime.datetime(2018, 9, 24, 9)
    monday_at_910 = datetime.datetime(2018, 9, 24, 9, 10)
    monday_at_1150 = datetime.datetime(2018, 9, 24, 11, 50)
    monday_at_12 = datetime.datetime(2018, 9, 24, 12)
    monday_at_13 = datetime.datetime(2018, 9, 24, 13)
    monday_at_14 = datetime.datetime(2018, 9, 24, 14)
    monday_at_16 = datetime.datetime(2018, 9, 24, 16)

    tw_60 = work_hour_typical_week(60)
    assert 9 == tw_60._get_index_from_datetime(monday_at_9)
    assert 12 == tw_60._get_index_from_datetime(monday_at_12)
    assert tw_60.is_busy(monday_at_9)
    assert not tw_60.is_busy(monday_at_12)
    assert tw_60.get_time_interval(monday_at_9) == tw_60.get_time_interval(monday_at_910)

    assert (
        tw_60.get_busy_intervals(monday_at_8, monday_at_12)
        == tw_60.get_busy_intervals(monday_at_9, monday_at_12)
        == tw_60.get_busy_intervals(monday_at_9, monday_at_13)
        == tw_60.get_busy_intervals(monday_at_8, monday_at_13))
    assert (
        tw_60.get_idle_intervals(monday_at_9, monday_at_16)
        == tw_60.get_idle_intervals(monday_at_12, monday_at_16)
        == tw_60.get_idle_intervals(monday_at_12, monday_at_14)
        == tw_60.get_idle_intervals(monday_at_9, monday_at_16)
    )


def test_external_operations():
    # make sure idle time AV(tw_union) <= AV(tw) for tw in tw_1, tw_2
    # make sure idle time AV(tw_intersection) >= AV(tw) for tw in tw_1, tw_2
    tw_60 = work_hour_typical_week(60)
    tw_30 = work_hour_typical_week(30)

    tw_union = tw_30 + tw_60
    tw_intersection = tw_30 * tw_60
    assert tw_30 == tw_union
    assert tw_30 == tw_intersection


def test_example():
    def example_1():
        from weekly_calendar import WeeklyCalendar
        from datetime import datetime, timedelta

        now = datetime.now()
        typical_week = WeeklyCalendar(resolution_in_minutes=60)

        assert typical_week.is_idle(now)
        typical_week.add_busy_interval(now, now + timedelta(hours=3))
        assert typical_week.is_busy(now)
        busy_intervals = typical_week.get_busy_intervals(now, now + timedelta(hours=5))
        assert len(busy_intervals) == 1
        idle_intervals = typical_week.get_idle_intervals(now, now + timedelta(hours=5))
        assert len(idle_intervals) == 1

    def example_2():
        from weekly_calendar import WeeklyCalendar

        tw_60 = WeeklyCalendar(resolution_in_minutes=60)
        tw_30 = WeeklyCalendar(resolution_in_minutes=30)
        # resulting objects will have the lowest resolution
        tw_union = tw_30 + tw_60
        tw_intersection = tw_30 * tw_60

    def example_3():
        from weekly_calendar import WeeklyCalendar

        tw_60 = WeeklyCalendar(resolution_in_minutes=60)
        tw_60_to_30 = tw_60.copy(resolution_in_minutes=30)

    def example_4():
        tw = WeeklyCalendar()
        str_repr = tw.dumps()
        tw_loaded = WeeklyCalendar.loads(str_repr)
        # checks equal resolution, bitmap, and extra parameters
        assert tw == tw_loaded
    example_1()
    example_2()
    example_3()
    example_4()


test_internals()
test_rescaling()
test_add_busy_interval()
test_external_operations()
test_example()
