""" Queries the National Weather Service API to retrieve the day's forecast:
        https://www.weather.gov/documentation/services-web-api
This is a 100% free service, but it's only available in the US.
"""
import os
import sys
import time
from datetime import datetime as dt
import argparse
import textwrap
from itertools import zip_longest
import requests

MAX_RETRIES = 3
# A 5 second timeout should work for most purposes, but if you have a
# particularly slow connection you may need to increase this value
TIMEOUT = 5

def make_request(url: str)->dict:
    """ Input:
            url: str - a URL which will return a JSON document
        Output:
            returns a dictionary containing the requested data
    """
    for i in range(MAX_RETRIES):
        req = requests.get(url, timeout=TIMEOUT)
        # This checks to see if the request returned a successful status code
        try:
            req.raise_for_status()
            break
        # If there was an unsuccessful status code:
        #   - if we've tried less than MAX_RETRIES times, then the program will
        #     sleep for 2 seconds
        #   - if we've tried MAX_RETRIES times, then the program will raise
        #     a HTTPError
        except requests.HTTPError as e:
            if i < (MAX_RETRIES-1):
                time.sleep(2)
            else:
                raise e
    return req.json()

def get_point_data():
    """ Gets metadata for the given point. This includes the urls we use to
    request forecasts.

    Note:
        If you want to get an accurate weather forecast from this, you gotta
        have environment variables called LATITUDE and LONGITUDE which store
        the latitude and longitude respectively (as you'd expect).
        If no LATITUDE and LONGITUDE environment variables exist, it defaults
        to the latitude and longitude of the Swetsville Zoo.
    """
    latitude = os.getenv('LATITUDE', '40.523')
    longitude = os.getenv('LONGITUDE', '-104.99')
    url = f'https://api.weather.gov/points/{latitude},{longitude}'
    point_data = make_request(url)
    return point_data

def get_hourly_forecast():
    """ Returns a list of dictionaries, each of which contains forecast data for
    a given hour.
    """
    point_data = get_point_data()
    hourly_url = point_data['properties']['forecastHourly']
    hourly_data = make_request(hourly_url)
    periods = hourly_data['properties']['periods']
    stripped_periods = strip_old_data(periods)
    return stripped_periods

def strip_old_data(periods: list) -> list:
    """ Input:
            periods: a list of dictionaries, each of which contains forecast
                data for a given hour.
        Output:
            stripped_data: list of dicts - periods, but with the forecast data
                for previous hours stripped away
    """
    # the API can lag behind, so the first entry might be for an hour that's
    # already passed
    for index, period in enumerate(periods):
        end_time = dt.fromisoformat(period['endTime'])
        now = dt.now(tz=end_time.tzinfo)
        if end_time < now:
            continue
        else:
            stripped_data = periods[index:]
            return stripped_data

def get_7_day_forecast() -> list:
    """ Input:
            None
        Output:
            periods: list of dicts - the 7-day forecast. Each dict contains the
                forecast for a 12 hour period: either 6am-6pm or 6pm-6am.
    """
    point_data = get_point_data()
    weekly_url = point_data['properties']['forecast']
    weekly_data = make_request(weekly_url)
    periods = weekly_data['properties']['periods']
    # From what I've seen, the 7 day forecast returns 14 periods, and the first
    # period is always the current period - that being said, it doesn't hurt to
    # be a, little paranoid, so we'll double check.
    stripped_periods = strip_old_data(periods)
    return stripped_periods

def quick_7_day_formatting(
        col_limit: int = 7,
        col_width: int = 20,
        col_padding: int = 5,
        alignment: str = 'left',
        include_current_period: bool = False,
        include_tonight: bool = True,
        start_index: int = 0,
        end_index: int = -1,
        # TODO: temp_to_c: bool = False,
        include_day: bool = True,
        include_night: bool = False,
        data_fields: list = [
            'name',
            'temperature',
            'temperatureTrend',
            'windSpeed',
            'windDirection',
            'shortForecast'
            ]) -> list:
    """ Input:
            col_limit: int - the number of columns worth of data to return.
            col_width: int - the weather for each period will be given a column.
                This value determines the width of the column.
            col_padding: int - the number of spaces separating each column from
                the next.
            alignment: str - valid values: "left", "right", "center".
                if 'left', the text in the columns will be aligned to the left.
                If 'right', thet text will be aligned to the right, and if
                'center', it will be alligned in the center.
            include_current_period: bool - if True, we include the current
                period. If False, the current period is omitted.
                This is here so you can make the current weather bigger and more
                verbose.
            include_tonight: bool - we might not want to include the forecast
                for EVERY night, since space is at a premium and we don't
                want to make our mirror too crowded with text, but it does
                make sense to want to include tonight's forecast.
                If true, we include tonight's forecast. If false, we handle it
                as dictated by the include_day and include_night variables. 
            start_index: int - after filtering has ocurred (removing night
                periods, etc.), this is the index of the first item that should
                be returned
            end_index: int - after filtering has ocurred (removing night
                periods, etc.), this is the index of the last item that should
                be returned
            temp_to_c: bool - if True, the temperature is displayed in degrees
                celsius. Otherwise it is displayed in degrees fahrenheit.
            include_day: bool - if True, we include the periods from 6am to 6pm.
                If False, these periods are discarded (which you probably don't
                want, but I'm including this option anyway).
            include_night: bool - if True, we include the periods from 6pm to
                6am. If False, these periods are discarded (less information,
                but it saves space).
            data_fields: list of strings - the names of the fields that should
                be included in the text representation of the weather forecast
                returned to the user. The data for each period will be presented
                in the order (from top to bottom) in which they appear in
                data_fields.
                These must be valid keys for the dictionary returned by the NWS
                API:
                    name: the name of the period (i.e., Today, Thursday Night,
                        Wednesday)
                    temperature
                    temperatureTrend: whether the temp is rising/falling/None.
                    windSpeed: usually a range, like '6 to 12 mph'
                    windDirection: compass direction, i.e. 'SSW'
                    shortForecast: a short description of the forecast. An
                        example:
                            Mostly Sunny then Chance Showers And Thunderstorms
                    detailedForecast: a more verbose description of the
                        forecast. An example:
                            A chance of showers and thunderstorms after noon.
                            Mostly sunny, with a high near 86.
        Output:
            cols: list of lists - each entry is a list containing the strings
                that make up the forecast column.

    This returns a string containing a rough and dirty representation of the
    forecast.
    """
    periods = get_7_day_forecast()
    cols = []
    for period in periods:
        # Including things that might be skipped otherwise
        if include_current_period and (period['number'] == 1):
            pass
        elif include_tonight and (period['name'] == 'Tonight'):
            pass
        # Skipping things that we don't want to include
        elif (not include_current_period) and (period['number'] == 1):
            continue
        elif (not include_day) and period['isDaytime']:
            continue
        elif (not include_night) and (not period['isDaytime']):
            continue
        # Add everything that made it through the filter to our column list
        cols.append(
            format_column(
                period,
                data_fields,
                col_width))

    # We make a lambda function called 'just' which will pad our columns to
    # the right length using the appropriate justification method.
    padded_width = col_width + col_padding
    if alignment == 'left':
        just = lambda x: x.ljust(padded_width) if x else ' '*(padded_width)
    elif alignment == 'right':
        just = lambda x: x.rjust(col_width + col_padding)
    elif alignment == 'center':
        just = lambda x: x.center(col_width + col_padding)
    else:
        raise ValueError('''
        Invalid value for "alignment". Valid values are: left, right, center''')

    # Here we're slicing the list if the user provided a start_index and
    # end_index
    cols = cols[start_index:end_index]
    # Here we're limiting the number of columns returned
    cols = cols[:col_limit]
    # This is a bit gross, but we're just turning our list of columns into
    # one block of text
    just_cols = [''.join([just(j) for j in i]) for i in zip_longest(*cols)]
    return '\n'.join(just_cols)

def format_column(
        period: dict,
        data_fields: list,
        col_width: int):
    """ Input:
            period: dict - the data for the period we want to format as a
                column
            data_fields: list - the data fields we want to include in the
                column
            col_width: int - the width of the column

    This takes a dictionary that was returned by the API and formats it such
    that it includes only the data fields specified by data_fields, and such
    that the width of the column does not exceed col_width.
    """
    wrap = textwrap.TextWrapper(width=col_width)

    # This is for handling the temperature.
    # The information is split across multiple fields, so we combining them
    # into one line here.
    temp_template = '{temperature} º{temperatureUnit}'
    temp_str = temp_template.format(**period)
    if 'temperatureTrend' in data_fields:
        if period['temperatureTrend']:
            temp_str += f" and {period['temperatureTrend']}"
        data_fields.remove('temperatureTrend')
    period['temperature'] = temp_str

    # Same as above, but for wind.
    # It doesn't make sense to have the wind direction on a separate line, IMO.
    # TODO: May include a CLI option for toggling this, but for now we'll just
    # smoosh them together.
    if ('windSpeed' in data_fields) and ('windDirection' in data_fields):
        wind_str = period['windSpeed'] + ' ' + period['windDirection']
        period['windSpeed'] = wind_str
        data_fields.remove('windDirection')

    return [line for key in data_fields for line in wrap.wrap(str(period[key]))]

def forecast_handler(args: argparse.Namespace):
    """ Input:
            args: argparse.Namespace - contains the attributes from our
                argument parser
        Output:
            writes the forecast to stdout

    This takes the CLI arguments provided by the user, and formats the forecast
    using them. The forecast for each period is formatted to fit in a column,
    and lal the columns are joined together to form one block of text.
    """
    if args.clear_fields:
        data_fields = []
    else:
        data_fields = [
            'name',
            'temperature',
            'temperatureTrend',
            'windSpeed',
            'windDirection',
            'shortForecast'
            ]
    if args.field_names:
        data_fields += [i for i in args.field_names if i not in data_fields]
    if args.remove_field_names:
        data_fields = [i for i in data_fields if i not in args.remove_field_names]

    forecast = quick_7_day_formatting(
        col_limit=args.col_limit,
        col_width=args.col_width,
        col_padding=args.col_padding,
        alignment=args.alignment,
        include_current_period=args.include_current_period,
        include_tonight=args.include_tonight,
        start_index=args.start,
        end_index=args.end,
        include_day=args.include_day,
        include_night=args.include_night,
        data_fields=data_fields,
    )
    sys.stdout.write(forecast)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        '-n',
        '--number-of-columns',
        dest='col_limit',
        type=int,
        default=5,
        help='''
        The number of columns that should be returned. With the default
        behavior this will return one day's forecast per column.
        '''
    )
    parser.add_argument(
        '-w',
        '--column-width',
        dest='col_width',
        type=int,
        default=20,
        help='''
        the weather for each period will be given a column. This value
        specifies the width of each column.
        '''
    )
    parser.add_argument(
        '-p',
        '--column-padding',
        dest='col_padding',
        type=int,
        default=5,
        help='''The number of spaces separating each column from the next.
        '''
    )
    parser.add_argument(
        '-a',
        '--alignment',
        choices=['left', 'right', 'center'],
        default='left',
        help='''
        This specifies how the text in the columns should be aligned. Valid
        options are 'left','right', and 'center'.
        '''
    )
    parser.add_argument(
        '-c',
        '--include-current-period',
        action='store_true',
        help='''
        Whether the current weather should be included.
        The default behavior is to not include the current weather so that it
        can be displayed separately and be made bigger and more visible.
        To return only the current weather, you would use: -c -n 1
        '''
    )
    parser.add_argument(
        '-rtn',
        '--remove-tonight-exception',
        dest='include_tonight',
        action='store_false',
        help='''
        The default behavior of this program is to omit nighttime forecasts with
        the exception of "tonight".
        Space is at a premium, and we don't want to make our mirror too crowded
        with text, but it does make sense to want to include tonight's forecast
        (at least to this humble programmer).
        This argument overrides that behavior, causing the "tonight" period to
        be handled in the same way as any other period.
        '''
    )
    parser.add_argument(
        '-s',
        '--start',
        type=int,
        default=0,
        help='''
        The API will return a number of periods. These will be filtered. With
        the default behavior, the night values will be removed (with the 
        exception of the forecast for "tonight").
        This argument specifies the index of the first item in this list of
        periods that should be included. With the default behavior, a value
        of 0 would be the current time period, a value of 1 would be the next
        daytime period, etc.
        IMPORTANT: THIS HAPPENS AFTER EVERY OTHER OPERATION FILTERING THE PERIOD
        LIST!
        '''
    )
    parser.add_argument(
        '-e',
        '--end',
        type=int,
        default=-1,
        help='''
        The API will return a number of periods. 
        This argument specifies the index of the last item in this list of
        periods that should be included (note that the first item is 0).
        IMPORTANT: THIS HAPPENS AFTER EVERY OTHER OPERATION FILTERING THE PERIOD
        LIST!
        '''
    )
    parser.add_argument(
        '-inp',
        '--include-night-periods',
        action='store_true',
        dest='include_night',
        help='''
        The default behavior of this progam is to omit nighttime forecast
        periods with the exeption of "tonight".
        This argument will cause the nighttime forecast periods to be included.
        Note that this will cause the program to output a much larger block
        of text. 
        '''
    )
    parser.add_argument(
        '-rdp',
        '--remove-day-periods',
        action='store_false',
        dest='include_day',
        help='''
        The default behavior of this progam is to include daytime forecast
        periods. This argument will cause the daytime periods to be omitted.
        '''
    )
    ########################
    # Specifying data fields
    ########################
    field_names = parser.add_argument_group(
        title='Field Names',
        description='''
        The user can override the default data fields using these arguments:

            --clear-fields: clears the default data fields list completely, 
                so the user can specify the exact fields, and the exact order
                of fields they would like to see.
                This requires the user to be more verbose.

            --include-[field name]: will include the field name specified. 
                example: --include-temperatureTrend

            --remove-[field name]: will remove the field name specified.
                Probably used to make small modifications to the default
                data fields list (removing windDirection, for example)
                    example: --exclude-windDirection

        The default data fields are:
            - 'name', 'temperature', 'temperatureTrend', 'windSpeed', 
              'windDirection', and 'shortForecast'
        
        The valid field names are:
            name: the name of the period (i.e., Today, Thursday Night, Wednesday)
            temperature: the temperature. Always in ºF as far as I can tell.
            temperatureTrend: whether the temp is rising/falling/None.
            windSpeed: usually a range, like '6 to 12 mph'
            windDirection: compass direction, i.e. 'SSW'
            shortForecast: a short description of the forecast. An
                example:
                    Mostly Sunny then Chance Showers And Thunderstorms
            detailedForecast: a more verbose description of the forecast. 
                example:
                    A chance of showers and thunderstorms after noon. Mostly 
                    sunny, with a high near 86.
        ''')
    field_names.add_argument(
        '-cf',
        '--clear-fields',
        help='''
        clears the default data fields list completely, so the user can specify
        the exact fields, and the exact order of fields they would like to see.
        ''',
        action='store_true'
    )
    #####################
    # Fields to include
    ####################
    field_names.add_argument(
        '-in',
        '--include-name',
        help='''
        This indicates that we should include the 'name' field in the forecast.
        ''',
        action='append_const',
        const='name',
        dest='field_names'
    )
    field_names.add_argument(
        '-it',
        '--include-temperature',
        help='''
        This indicates that we should include the 'temperature' field in the
        forecast.
        ''',
        action='append_const',
        const='temperature',
        dest='field_names'
    )
    field_names.add_argument(
        '-itt',
        '--include-temperatureTrend',
        help='''
        This indicates that we should include the 'temperatureTrend' field in
        the forecast.
        ''',
        action='append_const',
        const='temperatureTrend',
        dest='field_names'
    )
    field_names.add_argument(
        '-iw',
        '--include-windSpeed',
        help='''
        This indicates that we should include the 'windSpeed' field in the
        forecast.
        ''',
        action='append_const',
        const='windSpeed',
        dest='field_names'
    )
    field_names.add_argument(
        '-iwd',
        '--include-windDirection',
        help='''
        This indicates that we should include the 'windDirection' field in the
        forecast.
        ''',
        action='append_const',
        const='windDirection',
        dest='field_names'
    )
    field_names.add_argument(
        '-is',
        '--include-shortForecast',
        help='''
        This indicates that we should include the 'shortForecast' field in the
        forecast.
        ''',
        action='append_const',
        const='shortForecast',
        dest='field_names'
    )
    field_names.add_argument(
        '-id',
        '--include-detailedForecast',
        help='''
        This indicates that we should include the 'detailedForecast' field in
        the forecast.
        ''',
        action='append_const',
        const='detailedForecast',
        dest='field_names'
    )
    ###################
    # Fields to remove
    ###################
    # I expect that the '--remove-[field name]' arguments will only be used
    # to edit the default data field list. Since it's removing fields from
    # the data fields list the only way for the user to use this to remove a
    # field that isn't in the default data fields list would be for them to
    # first add it, and then remove it.
    # I'll include all the fields anyway, but if anyone ends up using -rtt
    # I'll be surprised and also slightly curious about what the heck you're
    # doing.
    field_names.add_argument(
        '-rn',
        '--remove-name',
        help='''
        This indicates that we should remove the 'name' field from the forecast.
        ''',
        action='append_const',
        const='name',
        dest='remove_field_names'
    )
    field_names.add_argument(
        '-rt',
        '--remove-temperature',
        help='''
        This indicates that we should remove the 'temperature' field from the
        forecast.
        ''',
        action='append_const',
        const='temperature',
        dest='remove_field_names'
    )
    field_names.add_argument(
        '-rtt',
        '--remove-temperatureTrend',
        help='''
        This indicates that we should remove the 'temperatureTrend' field from
        the forecast.
        ''',
        action='append_const',
        const='temperatureTrend',
        dest='remove_field_names'
    )
    field_names.add_argument(
        '-rw',
        '--remove-windSpeed',
        help='''
        This indicates that we should remove the 'windSpeed' field from the
        forecast.
        ''',
        action='append_const',
        const='windSpeed',
        dest='remove_field_names'
    )
    field_names.add_argument(
        '-rwd',
        '--remove-windDirection',
        help='''
        This indicates that we should remove the 'windDirection' field from the
        forecast.
        ''',
        action='append_const',
        const='windDirection',
        dest='remove_field_names'
    )
    field_names.add_argument(
        '-rs',
        '--remove-shortForecast',
        help='''
        This indicates that we should remove the 'shortForecast' field from the
        forecast.
        ''',
        action='append_const',
        const='shortForecast',
        dest='remove_field_names'
    )
    field_names.add_argument(
        '-rd',
        '--remove-detailedForecast',
        help='''
        This indicates that we should remove the 'detailedForecast' field from
        the forecast.
        ''',
        action='append_const',
        const='detailedForecast',
        dest='remove_field_names'
    )
    args = parser.parse_args()
    forecast_handler(args)
