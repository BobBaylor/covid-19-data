""" covid-19-counties.py

workon covid
get latest data by running
git pull
from https://github.com/nytimes/covid-19-data.git

which updates csv files from the New York Times
us-counties.csv:
    date,county,state,fips,cases,deaths

us-states.csv:
    date,state,fips,cases,deaths

us.csv:
    date,cases,deaths

pandas quickstart from
https://www.fullstackpython.com/blog/learn-pandas-basic-commands-explore-covid-19-data.html
"""

import os
from datetime import datetime
from math import ceil
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

if __name__ == '__main__':
    try:
        import docopt
    except ModuleNotFoundError:
        print(f'docopt import failed for {__name__}. Use an environment with docopt installed, please.')


USAGE_TEXT = """
 Usage:
  covid-19-counties.py  [--counties=<C>] [--debug=<D>][--get] [--lines] [--log] [--multi=<M>] [--norm] [--state=<S>]
  covid-19-counties.py -h | --help
  covid-19-counties.py -v | --version

 Options:
  -c --counties <C>       Choose counties, comma sep, use quotes around whole thing [default: Santa Clara, Alameda, San Mateo, San Francisco, Contra Costa, Marin, Sonoma, Napa]
  -d --debug <D>          print opts,
  -g --get                Get current NY Times data.
  -h --help               Show this screen.
  -l --lines              Show the data in tabular form.
  -o --log                Use log Y scale
  -m --multi <M>          Multi all on one plot. c=cases, d=deaths. lower case for new, upper for totals.
  -n --norm               Plot normalized to population
  -s --state <S>          State [default: California]
  -v --version            show the version.
    """

def get_data():
    """ curl https://opendata.ecdc.europa.eu/covid19/casedistribution/csv/ > req.csv
    """
    print('Try\ngit fetch upstream\ninstead, Bob\n')




def show_county_stats(opts, df, county):
    """the grim stats of the selected df """
    df3 = df[df['County'] == county.strip()]
    if opts['--norm']:
        print(f'total cases:  {df3.iloc[-1]["total cases"]:0.2f} %')
        print(f'total deaths: {df3.iloc[-1]["total deaths"]:0.2f} %')
    else:
        print(f'total cases:  {df3.iloc[-1]["total cases"]:8,}')
        print(f'total deaths: {df3.iloc[-1]["total deaths"]:8,}')


def display_one_county(opts, df, county):
    """Plot/list/stat a single county on a single graph
    """
    # select a single county
    df3 = df[df['County'] == county]
    print(f'\n{county} {df3.iloc[-1]["fips"]:8,}')
    if opts['--lines']:
        show_county_stats(opts, df3, county)


def plot_multi_counties(opts, df, counties, pops):
    """Plot/stat all selected counties on a single graph.
    """
    for county in counties:     # show the stats
        df2 = df[df['County'] == county]
        print(f'\n{county}')
        show_county_stats(opts, df, county)

    # we've already filtered out all but the requested State
    df3 = df[df['County'].isin(counties)]   # keep only the counties I care about
    df4 = df3[['Date', 'County', 'daily cases', 'daily deaths', 'total cases', 'total deaths', 'fips']]

    y_col = choose_series(opts)
    norm_str = ' (% of pop)' if opts['--norm'] else ' (count)'
    title = f'{y_col}{norm_str}'

    fig, ax = plt.subplots(figsize=(8, 5))          # 8 wide by 4 tall seems good

    # df_sorted = df4.sort_values(y_col, ascending=False)
    # groupby is magic.   https://realpython.com/pandas-groupby/
    for key, grp in df4.groupby(['County']):
    # for key, grp in df_sorted.groupby(['County']):
        if opts['--norm']:
            y_str = f'{grp.iloc[-1][y_col]:0.3f} '
        else:
            y_str = f'{int(grp.iloc[-1][y_col]):8,} '
        ax.plot(grp['Date'], grp[y_col], label=y_str+key, linewidth=7)

    ax.legend()                                     # show the legend
    if opts['--log']:
        ax.set_yscale('log')
        plt.ylim(bottom=5)
        # plt.ylim(bottom=int(opts['--threshold'])//2)
    else:
        plt.autoscale()
    ax.set_title(title)

    ax.xaxis.set_minor_locator(mdates.WeekdayLocator(byweekday=mdates.MO))  # every week x ticks
    ax.xaxis.set_major_locator(mdates.MonthLocator())  # major x: the first of every month
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b 1')) # x labels month day

    # plt.ylim(bottom=int(opts['--threshold'])//2)
    plt.grid(which='major', axis='both')             # show both major axis
    plt.grid(which='minor', axis='y', ls='dotted')   # show y minor as dotted
    fig.autofmt_xdate()       # rotate, right align, and leave room for date labels
    plt.show()


def choose_series(opts):
    """ CLI can choose what to graph on the multi-plot. If nothing chosen, then
        return 'total cases'
    """
    return {'c':'daily cases',
             'd':'daily deaths',
             'C':'total cases',
             'D':'total deaths'}.get(opts['--multi'], 'total cases')

def get_county_list(opts, df, column):
    """CLI can choose specific counties, or just enter a number N to see the N highest
    """
    top_number = None
    try:
        top_number = int(opts['--counties'])
    except ValueError:
        pass
    if top_number:
        # could these 2 lines be df.nlargest(top_number, column)   ?
        # maybe after a groupby County?
        df_sorted = df.sort_values(column, ascending=False).drop_duplicates('County')
        counties = df_sorted.County.tolist()[:top_number]
    else:
        counties = [county.strip() for county in opts['--counties'].split(',')]
    return counties


def get_populations():
    """ read a census csv of population (and a lot more) and package it into something
        I can use to normalize graphs.
    """
    # SUMLEV,REGION,DIVISION,STATE,COUNTY,STNAME,CTYNAME,CENSUS2010POP,ESTIMATESBASE2010, ...
    # 050,4,9,06,085,California,Santa Clara County,1781642,1781686,1786040,1812054,...
    POPULATION_FILE = 'co-est2019-alldata.csv'
    df = pd.read_csv(POPULATION_FILE, encoding='ISO-8859-1')
    df['population'] = df['POPESTIMATE2019']
    df['state'] = df['STNAME']
    df['County'] = df['CTYNAME']
    # construct a fips series to make it easy to mathc the fips in the covid database
    df['fips'] = df['STATE']*1000 + df['COUNTY']
    # only keep what I care about
    df = df[[ # 'state',
              #'County',
             'fips',
             'population',
             ]]
    return df


def test(opts):
    """Do the various things as requested
    """
    print('*'*60, '\n'+'*'*60)
    if opts['--debug']:
        print(opts)

    DATA_FILE = 'us-counties.csv'

    if opts['--get']:
        get_data()       # go ask the WHO server for a new csv and save it

    df = pd.read_csv(DATA_FILE, encoding='ISO-8859-1')
    f_date = datetime.fromtimestamp(os.path.getmtime(DATA_FILE))
    print(f'Data was retrieved {f_date:%B %d, %Y at %H:%M %p}')
    # date,county,state,fips,cases,deaths
    # 2020-01-21,Snohomish,Washington,53061,1,0

    # make plotable date and rename the cases and deaths for plotting
    # I do it before selecting by county to avoid the SettingWithCopy warning
    # which is pandas saying 'you're modifying a copy, not the actual dataset'
    df['Date'] = pd.to_datetime(df.date, format='%Y-%m-%d')

    df['total deaths'] = df['deaths']
    df['total cases'] = df['cases']
    df['County'] = df['county']
    max_date = df['Date'].max()
    df.sort_values(by=['state','county','Date'], inplace=True)
    df['daily deaths'] = df.deaths.diff().fillna(0).astype(int)
    df['daily cases'] = df.cases.diff().fillna(0).astype(int)
    df['fips'] = df.fips.fillna(0).astype(int)
    print(f'Most recent date point is {max_date:%B %d, %Y at %H:%M %p}')

    # todo: pull in test counts (both pos and neg) From where?

    # only keep what I care about
    df = df[['state',
             'County',
             'Date',
             'total cases',
             'total deaths',
             'daily cases',
             'daily deaths',
             'fips',
             ]]

    # smooth the daily data to a 7 day rolling average
    df['daily cases'] = df['daily cases'].rolling(window=7).sum().divide(7.0)
    df['daily deaths'] = df['daily deaths'].rolling(window=7).sum().divide(7.0)
    # keep only the requested state
    df = df[df['state'] == opts['--state']]

    pops = get_populations()
    df = pd.merge(df, pops, on='fips')
    # normalize by population, if requested
    if opts['--norm']:
        for col in ['total cases', 'total deaths', 'daily cases', 'daily deaths']:
            df[[col]] = df[[col]].div(df.population, axis=0)
            df[[col]] = df[[col]].mul(100.0)

    y_col = choose_series(opts)
    counties = get_county_list(opts, df, y_col)
    # filter out small numbers of cases in a day
    if opts['--norm']:
        df = df[df['daily cases'] >= 0]
    else:
        df = df[df['daily cases'] >= 2]

    plt.close('all')
    if opts['--multi']:
        plot_multi_counties(opts, df, counties, pops)
    else:
        for county in counties:
            display_one_county(opts, df, county)


if __name__ == '__main__':
    opts = docopt.docopt(USAGE_TEXT, version='0.0.4')
    test(opts)
