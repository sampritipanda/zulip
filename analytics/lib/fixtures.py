from __future__ import division, absolute_import

from zerver.models import Realm, UserProfile, Stream, Message
from analytics.models import InstallationCount, RealmCount, UserCount, StreamCount
from analytics.lib.counts import CountStat
from analytics.lib.time_utils import time_range

from datetime import datetime
from math import sqrt
from random import gauss, random, seed

from six.moves import range, zip

def generate_time_series_data(length, business_hours_base, non_business_hours_base,
                              growth=1, autocorrelation=0, spikiness=1, holiday_rate=0,
                              frequency=CountStat.HOUR, is_gauge=False):
    # type: (int, float, float, float, float, float, float, str, bool) -> List[int]
    """
    Generate semi-realistic looking time series data for testing analytics graphs.

    length -- Number of data points returned.
    business_hours_base -- Average value during a business hour (or day) at beginning of
        time series, if frequency is CountStat.HOUR (CountStat.DAY, respectively).
    non_business_hours_base -- The above, for non-business hours/days.
    growth -- Ratio between average values at end of time series and beginning of time series.
    autocorrelation -- Makes neighboring data points look more like each other. At 0 each
        point is unaffected by the previous point, and at 1 each point is a deterministic
        function of the previous point.
    spikiness -- 0 means no randomness (other than holiday_rate), higher values increase
        the variance.
    holiday_rate -- Fraction of points randomly set to 0.
    frequency -- Should be CountStat.HOUR or CountStat.DAY.
    is_gauge -- If True, return partial sum of the series.
    """
    if length < 2:
        raise ValueError("length must be at least 2")
    if frequency == CountStat.HOUR:
        seasonality = [non_business_hours_base] * 24 * 7
        for day in range(5):
            for hour in range(8):
                seasonality[24*day + hour] = business_hours_base
    elif frequency == CountStat.DAY:
        seasonality = [business_hours_base]*5 + [non_business_hours_base]*2
    else:
        raise ValueError("Unknown frequency: %s" % (frequency,))
    growth_base = growth ** (1. / (length-1))
    values_no_noise = [seasonality[i % len(seasonality)] * (growth_base**i) for i in range(length)]

    seed(26)
    noise_scalars = [gauss(0, 1)]
    for i in range(1, length):
        noise_scalars.append(noise_scalars[-1]*autocorrelation + gauss(0, 1)*(1-autocorrelation))

    values = [0 if random() < holiday_rate else int(v + sqrt(v)*noise_scalar*spikiness)
              for v, noise_scalar in zip(values_no_noise, noise_scalars)]
    if is_gauge:
        for i in range(1, length):
            values[i] = values[i-1] + values[i]
    else:
        values = [max(v, 0) for v in values]
    return values

def bulk_create_realmcount(property, subgroup, last_end_time, frequency, interval, values, realm):
    # type: (str, str, datetime, str, str, List[int], Realm) -> None
    end_times = time_range(last_end_time, last_end_time, frequency, len(values))
    RealmCount.objects.bulk_create([
        RealmCount(realm=realm, property=property, subgroup=subgroup, end_time=end_time,
                   interval=interval, value=value)
        for end_time, value in zip(end_times, values) if value != 0])
