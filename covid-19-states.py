""" covid-19-states.py

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
  covid-19-states.py  [--debug=<D>] [--lines] [--log] [--multi=<M>] [--norm] [--states=<S>]
  covid-19-states.py -h | --help
  covid-19-states.py -v | --version

 Options:
  -d --debug <D>          print opts,
  -h --help               Show this screen.
  -l --lines              Show the data in tabular form.
  -m --multi <M>          Multi all on one plot. c=cases, d=deaths. lower case for new, upper for totals.
  -n --norm               Plot normalized to population
  -o --log                Use log Y scale
  -s --states <S>         Choose states, comma sep, use quotes around whole thing [default: Arizona,California,Texas,Florida,Louisiana,Alabama,South Carolina,Mississippi,Idaho]
  -v --version            show the version.
    """


def show_state_stats(df, state):
    """the grim stats of the selected df """
    df3 = df[df['State'] == state.strip()]
    if opts['--norm']:
        print(f'total cases:  {df3.iloc[-1]["total cases"]:0.2f} %')
        print(f'total deaths: {df3.iloc[-1]["total deaths"]:0.2f} %')
    else:
        print(f'total cases:  {df3.iloc[-1]["total cases"]:8,}')
        print(f'total deaths: {df3.iloc[-1]["total deaths"]:8,}')


def display_one_state(opts, df, state):
    """Plot/list/stat a single state on a single graph
    """
    # select a single state
    print(f'\n{state}')
    df3 = df[df['State'] == state]
    if opts['--lines']:
        print(df3)
    show_state_stats(df3, state)


def plot_multi_states(opts, df, state_list):
    """Plot/stat all selected state_list on a single graph.
    """
    for state in state_list:
        print(f'\n{state}')
        show_state_stats(df, state)

    df3 = df[df['State'].isin(state_list)]
    df4 = df3[['Date', 'State', 'daily cases', 'daily deaths', 'total cases', 'total deaths']]

    y_col = choose_column(opts)
    norm_str = ' (% of pop)' if opts['--norm'] else ' (count)'
    title = f'{y_col}{norm_str}'

    fig, ax = plt.subplots(figsize=(8, 5))          # 8 wide by 4 tall seems good

    # groupby is magic.   https://realpython.com/pandas-groupby/
    for key, grp in df4.groupby(['State']):
        if opts['--norm']:
            y_str = f'{grp.iloc[-1][y_col]:0.3f} '
        else:
            y_str = f'{int(grp.iloc[-1][y_col]):8,} '
        ax.plot(grp['Date'], grp[y_col], label=y_str+key, linewidth=7)

    ax.legend()                                     # show the legend
    if opts['--log']:
        ax.set_yscale('log')                            # log y axis to see slope
        plt.ylim(bottom=5)
    else:
        plt.autoscale()
    ax.set_title(title)

    ax.xaxis.set_minor_locator(mdates.WeekdayLocator(byweekday=mdates.MO))  # every week x ticks
    ax.xaxis.set_major_locator(mdates.MonthLocator())  # major x: the first of every month
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b 1')) # x labels month day

    plt.grid(which='major', axis='both')             # show both major axis
    plt.grid(which='minor', axis='y', ls='dotted')   # show y minor as dotted
    fig.autofmt_xdate()       # rotate, right align, and leave room for date labels
    plt.show()


def choose_column(opts):
    """ CLI can choose what to graph on the multi-plot. If nothing chosen, then
        return 'total cases'
    """
    return {'c':'daily cases',
             'd':'daily deaths',
             'C':'total cases',
             'D':'total deaths'}.get(opts['--multi'], 'total cases')

def get_state_list(opts, df, column):
    """CLI can choose specific states, or just enter a number N to see the N highest
    """
    top_number = None
    try:
        top_number = int(opts['--states'])
    except ValueError:
        pass
    if top_number:
        df_sorted = df.sort_values(column, ascending=False).drop_duplicates('State')
        # print('sorted\n', df_sorted)
        states = df_sorted.State.tolist()[:top_number]
    else:
        states = [State.strip() for State in opts['--states'].split(',')]
    return states


def get_populations():
    """ read a census csv of population and package it into something
        I can use to normalize graphs.
    """
    # state,Estimated_pop_2019,Census_pop_2010
    POPULATION_FILE = 'state_pops.csv'
    df = pd.read_csv(POPULATION_FILE, encoding='ISO-8859-1')
    df['population'] = df['Estimated_pop_2019']
    df['State'] = df['state']
    # only keep what I care about
    df = df[['State',
             'population',
             ]]
    # df3 = df[df['state'].isin(state_list)]  # filter out other states
    return df


def test(opts):
    """Do the various things as requested
    """
    print('*'*60, '\n'+'*'*60)
    if opts['--debug']:
        print(opts)

    DATA_FILE = 'us-states.csv'

    df = pd.read_csv(DATA_FILE, encoding='ISO-8859-1')
    f_date = datetime.fromtimestamp(os.path.getmtime(DATA_FILE))
    print(f'Data was retrieved {f_date:%B %d, %Y at %H:%M %p}')

    # date,State,state,fips,cases,deaths
    # 2020-01-21,Snohomish,Washington,53061,1,0

    # make plotable date and rename the cases and deaths for plotting
    # I do it before selecting by State to avoid the SettingWithCopy warning
    # which is pandas saying 'you're modifying a copy, not the actual dataset'
    df['Date'] = pd.to_datetime(df.date, format='%Y-%m-%d')

    df['total deaths'] = df['deaths']
    df['total cases'] = df['cases']
    df['State'] = df['state']
    max_date = df['Date'].max()
    df.sort_values(by=['State','Date'], inplace=True)
    df['daily deaths'] = df.deaths.diff().fillna(0).astype(int)
    df['daily cases'] = df.cases.diff().fillna(0).astype(int)
    print(f'Most recent date point is {max_date:%B %d, %Y at %H:%M %p}')

    # todo: pull in test counts (both pos and neg)  From where?

    # only keep what I care about
    df = df[['State',
             'Date',
             'total cases',
             'total deaths',
             'daily cases',
             'daily deaths',
             'fips',
             ]]

    df['daily cases'] = df['daily cases'].rolling(window=7).sum().divide(7.0)
    df['daily deaths'] = df['daily deaths'].rolling(window=7).sum().divide(7.0)

    pops = get_populations()
    df = pd.merge(df, pops, on='State')  # include the population data
    # normalize by population, if requested
    if opts['--norm']:
        for col in ['total cases', 'total deaths', 'daily cases', 'daily deaths']:
            df[[col]] = df[[col]].div(df.population, axis=0)
            df[[col]] = df[[col]].mul(100.0)

    y_col = choose_column(opts)
    state_list = get_state_list(opts, df, y_col)

    # filter out small numbers of cases in a day
    if opts['--norm']:
        df = df[df['daily cases'] >= 0]
    else:
        df = df[df['daily cases'] >= 2]


    plt.close('all')
    if opts['--multi']:
        plot_multi_states(opts, df, state_list)
    else:
        for state in state_list:
            display_one_state(opts, df, state)


if __name__ == '__main__':
    opts = docopt.docopt(USAGE_TEXT, version='0.0.4')
    test(opts)
