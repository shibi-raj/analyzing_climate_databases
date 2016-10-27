import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from peewee import *
from mpl_toolkits.basemap import Basemap, pyproj
# --------------- 
writing = False #  FLAG FOR OCEAN_BOX_TABLES
# ---------------  
from orm.ocean_box_tables import *
from time_series import *
from analysis import *

def process_years(years):
    """Utility to handle different inputs for years and generate title of 
    plot.
    """
    if isinstance(years,(list,tuple)):
        years = tuple(sorted(years))
    else:
        years = (years,years)
    date_min = str(years[0])+'-01-01'
    date_max = str(years[1])+'-12-31'
    return date_min,date_max

def obs_per_year(years,fig=None):
    """Get number of observations by year, add data to the fig, and return the 
    years and number data.
    """
    date_min,date_max = process_years(years)
    sql = "select strftime('%Y',date), count(name) "\
    + "from obsdata "\
    + "where date between '{}' and '{}' ".format(date_min,date_max) \
    + "group by strftime('%Y',date);"
    yrs, num = zip(*db_box.execute_sql(sql))

    if not fig:
        plt.figure()
        plt.subplot(111)
        plt.title('No. SST Observations by Year')
        plt.xlabel('Years')
        plt.ylabel('No. of SST Observations')
    label = 'No. of Observations {}-{}'.format(years[0],years[1])
    plt.plot(yrs,num,marker='o',alpha=.5,label=label)
    plt.legend(loc='upper left', frameon=False)
    if not fig:
        plt.show()
    return yrs, num

def boxes_per_year(years,fig=None):
    """Get number of boxes with (so far) any amount of data by year, add data to 
    the fig, and return the years and number data.
    """
    date_min,date_max = process_years(years)
    sql = "select strftime('%Y',date),count(distinct name) " \
    + "from obsdata "\
    + "where date between '{}' and '{}' ".format(date_min,date_max)\
    + "group by strftime('%Y',date);"
    yrs, num = zip(*db_box.execute_sql(sql))

    if not fig:
        plt.figure()
        plt.subplot(111)
        plt.title('No. Distinct Boxes by Year')
        plt.xlabel('Years')
        plt.ylabel('No. of Distinct Boxes')
    label = 'No. of Distinct Boxes {}-{}'.format(years[0],years[1])
    plt.plot(yrs,num,c='r',marker='o',alpha=.5,label=label)
    plt.legend(loc='upper left', frameon=False)
    if not fig:
        plt.show()
    return yrs, num

def sst_by_pentad(years,limit=1,name=None,fig=None,avg=True):
    """Plot avg(sst) vs. pentad.  Can specify name of a particular box."""
    if not fig:
        plt.figure()
        plt.subplot(111)
        plt.ylabel(r'$\degree$C')
        plt.xlabel(r'Pentad')
    
    if name:
        names = [name]
    else:
        names, counts = dense_boxes(years,limit=limit)
    
    for nm in names:
        if avg == True:
            pentads, ssts = mean_sst_by_pentad(years,name=nm)
            label = 'Avg SST\nBox {}\n{}-{}'.format(nm,years[0],years[1])
            plt.plot(pentads,ssts,marker='o',alpha=1,label=label)
        else:
            pentads, ssts = all_sst_by_pentad(years,nm)
            label = 'SST\nBox {}\n{}-{}'.format(nm,years[0],years[1])
            plt.title('SST by pentad, {}-{}'.format(years[0],years[1]))
            plt.scatter(pentads,ssts,c=ssts,marker='o',alpha=.05,label=label)
        plt.legend(loc='upper left', prop={'size':10}, frameon=False)
    if not fig:
        plt.show()

def stats_by_radius(radius,name,years,mean=True,std=True):
    # radius_data(radius,name,years)
    sst = [rd[3] for rd in radius_stats(radius,name,years)]
    return np.mean(sst), np.std(sst,ddof=1)

def plot_input(col_pairs,filename,csv=True,xlabel=None,ylabel=None,title=None,
        label=None):
    with open(filename,'r') as f:
        if csv:
            table = pd.read_csv(f)
    columns = table.columns
    # print(col_pairs)
    # Calculate standard error
    SE = 1.96*table[columns[1]]/table[columns[2]]**.5
    upper = np.array([])
    lower = np.array([])
    for cp in col_pairs:
        label = filename+': \n'
        for i,c in enumerate(cp):
            if c == 'SE':
                label = label+'SE'
                if i == 0:
                    x = SE
                if i == 1:
                    y = SE
                continue
            elif c == 0:
                upper = table[columns[c]] + SE
                lower = table[columns[c]] - SE
            if i == 0 and isinstance(c,int):
                x = table[columns[c]]
            elif i == 1 and isinstance(c,int):
                y = table[columns[c]]
            else:
                label = label + columns[c]
            
    # if not label:
    #     label = filename+': \n'+columns[cp[1]]+','+columns[cp[0]]
    # print(x)
    # print(y)
    if ylabel:
        plt.ylabel(ylabel)
    if xlabel:
        plt.xlabel(xlabel)
    if title:
        plt.title(title)
    plt.plot(x,y,label=label)
    print(upper)
    if upper.any():

        plt.plot(x,upper)
        plt.plot(x, lower)
    # plt.legend(loc='upper left', prop={'size':10}, frameon=False)

def plot_stats_by_radius():
    """The contents of this function are complete and simply put into this
    function without any testing.  If needed, will have to make the function
    work properly.
    """
    folder = './data_sets/analysis/std_radius/'
    pentads = range(1,2)
    for pentad in pentads:
        filename = 'std_radius_739_1853_pentad{}.txt'.format(pentad)
        filename = folder + filename

        plt.subplot(4,1,1)
        plot_input(((2,0),),filename,ylabel=r'Mean SST ($\degree$C)',
            title="Box 739_1853 pentad {}".format(pentad))
        
        plt.subplot(4,1,2)
        plot_input(((2,1),),filename,ylabel=r"STD(SST) ($\degree$C)")

        plt.subplot(4,1,3)
        plot_input(((2,'SE'),),filename,ylabel=r"SE ($\degree$C)")

        plt.subplot(4,1,4)
        plot_input(((2,3),),filename,ylabel="Count",xlabel="Radius (km)")

        plt.show()

def plot_sst_vs_year(name,years,pentad=None,label=None):
    avg_ssts,counts,yrs = mean_sst_by_year(name,years,pentad=pentad)
    title = "Box {}".format(name)
    if pentad:
        title = title + ", Pentad {}".format(pentad)
    title = title + ", {}-{}".format(years[0],years[1])
    plt.subplot(211)
    plt.title(title)
    plt.ylabel("Avg. SST")
    if label:
        plt.legend(loc='upper left', frameon=False)
        plt.plot(yrs,avg_ssts,label=label)
    else:
        plt.plot(yrs,avg_ssts)
    plt.subplot(212)
    plt.plot(yrs,counts)
    plt.ylabel("Counts")
    plt.xlabel("Year")

def plot_sim_trends(series,times,num_sims=10000,counts=None,xlabel=None,ylabel=None,
    residuals=False,plot_sims=True):
    """Plot data, regression fit (linear now), confidence slopes, background
    simulations for confidence interval, and residuals.
    """
    series = np.array(list(map(float,series)))
    times = np.array(list(map(float,times)))
    m,b,simulations,interval,slopes,std_err = sim_series(series,times,num_sims=num_sims)
    print(m,b,interval)

    # intercepts for upper and lower bounds of confidence interval
    b_up = series[0]-times[0]*interval[1]
    b_dn = series[0]-times[0]*interval[0]

    title = "Yearly Avg. Time Series for Box {} ".format(name)\
    +"\n95% confidence trend interval: ({},{}) ".format(
        round(interval[0],3),round(interval[1],3))\
    +"\nFit: m = {}, b = {} ".format(round(m,3),round(b,2))\
    +"\nSample variance: {} ".format(round(std_err,3))
    # +"\nSample variance: {} ".format(round(np.std(series,ddof=1),2))

    # add residuals plot
    if residuals == True:
        res = series - (m*times+b)
        plt.subplot(312)
        plt.ylabel('Residuals')
        plt.axhline(0)
        plt.scatter(times,res)
        plt.subplot(311)
    else:
        plt.subplot(311)

    # add data, fit, confidence slopes, and possibly background simulations
    plt.title(title)
    if xlabel:
        plt.xlabel(xlabel)
    if ylabel:
        plt.ylabel(ylabel)
    if plot_sims == True:
        for sim in simulations:
            plt.plot(times,sim,'gray',alpha=.1)
    plt.plot(times,series,'purple')
    plt.plot(times,times*m+b,'r')
    plt.plot(times,times*interval[0]+b_dn,'k')
    plt.plot(times,times*interval[1]+b_up,'k')
    
    # add counts plot
    if counts:
        plt.subplot(313)
        plt.ylabel('Counts')
        plt.plot(times,counts)
        plt.ylim(0.,30.)

    # print(slopes)
    # df = pd.DataFrame({'slopes':np.array(slopes)})
    # df.plot.hist(bins=num_sims//100)
    # plt.show()
    # print(m,stats.t.interval(0.95, len(slopes)-1, loc=np.mean(slopes), scale=stats.sem(slopes)))

def plot_sims_for_testing(series,times,num_sims=5):
    series = np.array(list(map(float,series)))
    times = np.array(list(map(float,times)))
    m,b,simulations,interval = sim_series(series,times,num_sims=num_sims)[0:4]
    for sim in simulations:
            slope, intercept = np.polyfit(times,sim,1)
            plt.plot(times,sim,'gray',alpha=.1)
            plt.plot(times,times*slope+intercept)

def plot_time_series(name,years,hmonth=None,plain=False,avg_on_yr=False):
    """Plot time series for a box in given year range."""
    n=6

    print(hmonth)

    if plain:
        ssts,dates = plain_time_series(name,years,hmonth=1)
        series = np.array(list(map(float,ssts)))
        times = np.array(list(map(float,dates)))

    elif avg_on_yr:
        pentads = conv_hmth_pentad(hmonth)
        avg_ssts,counts,yrs = mean_sst_by_year(name,years,pentads=pentads)
        
        # mean sst time series
        plt.subplot(n,1,1)
        plt.scatter(yrs,avg_ssts)
        series = np.array(list(map(float,avg_ssts)))
        times = np.array(list(map(float,yrs)))
        m, b, r_value, p_value, std_err = stats.linregress(times,series)

        plt.plot(times,times*m+b)

        # counts time series
        plt.subplot(n,1,2)
        plt.scatter(yrs,counts)

        # calculate autocorrelations of the data and plot vs. lag
        # ac = list()
        lags = list(range(1,len(avg_ssts)+1))
        # ts = pd.Series(np.array(avg_ssts))
        # for lag in lags:
        #     ac.append(ts.autocorr(lag))        
        # # autocorrelation vs. lag (line plot)
        # plt.subplot(n,1,3)
        # plt.xlim(0.,max(lags))
        # plt.ylim(-1.25,1.25)
        # plt.axhline(0.,c='black')
        # for (x,y) in zip(lags,ac):
        #     plt.plot([x,x],[0.,y],c='gray',linewidth='2')

        # plot residuals vs. time
        plt.subplot(n,1,3)
        res = series - (m*times+b)
        plt.scatter(times,res)
        plt.axhline(0.)
        plt.subplot(n,1,4)
        
        # plot autocorrelations of the residuals vs. lag
        acr = list()
        tsr = pd.Series(np.array(res))
        for lag in lags:
            acr.append(tsr.autocorr(lag))        
        plt.xlim(0.,max(lags))
        plt.ylim(-1.25,1.25)
        plt.axhline(0.,c='black')
        for (x,y) in zip(lags,acr):
            plt.plot([x,x],[0.,y],c='gray',linewidth='2')

        # plot of residuals vs. predicted values
        plt.subplot(n,1,5)
        plt.axhline(0)
        plt.plot(m*times+b,res)

        print(m,b)
        sys.stdout.flush()
        print()

def general_per_year(years):
    """Set up the figure any way you like."""
    # fig = plt.figure()
    plt.plot(yrs,ratios,marker='o',alpha=.5)
    plt.legend(loc='upper left', frameon=False)
    plt.show()

def plot_ols_by_decade(name,years,hmonth=1,avg_on_yr=True,half_decs=False):
    decs = decades(years,half_decs=half_decs)
    for decade in decs:
        print(decade)
        try:
            plot_time_series(name,decade,hmonth=hmonth,avg_on_yr=True)
        except:
            pass

def plot_hist(series):
    """Plot histogram of single data set.  Using to see visually is data close
    to normally distributed.
    """
    df = pd.DataFrame({'series':np.array(series)})
    df.plot.hist(bins=20)#.set_xlim(15,30)
    plt.show()



if __name__ == '__main__':
    timeseries = load_pickle_list(file='mid_atlantic_timeseries.p')
    times,series = zip(*timeseries)
    plt.plot(times,series)
    plt.show()
