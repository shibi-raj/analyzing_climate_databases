# --------------- 
writing = False #  FLAG FOR OCEAN_BOX_TABLES
# ---------------  
from analysis import *

# linfit.py - example of confidence limit calculation for linear regression fitting.
 
# References:
# - Statistics in Geography by David Ebdon (ISBN: 978-0631136880)
# - Reliability Engineering Resource Website:
# - http://www.weibull.com/DOEWeb/confidence_intervals_in_simple_linear_regression.htm
# - University of Glascow, Department of Statistics:
# - http://www.stats.gla.ac.uk/steps/glossary/confidence_intervals.html#conflim
 
import numpy as np
import matplotlib.pyplot as plt

def regressions(x,y,years,counts=None,residuals=None): 
    plot_opts = list()
    for opt in [counts,residuals]:
        if opt:
            plot_opts.append(True)
        else:
            plot_opts.append(False)
    n_plots = 1 + sum(plot_opts)
    m = 1
    # if x == None:
    #     # example data
    #     x = np.array([4.0,2.5,3.2,5.8,7.4,4.4,8.3,8.5])
    #     y = np.array([2.1,4.0,1.5,6.3,5.0,5.8,8.1,7.1])
    
    # fit a curve to the data using a least squares 1st order polynomial fit
    z = np.polyfit(x,y,1)
    p = np.poly1d(z)
    fit = p(x)

    # get the coordinates for the fit curve
    c_y = [np.min(fit),np.max(fit)]
    c_x = [np.min(x),np.max(x)]


    # predict y values of origional data using the fit
    p_y = z[0] * x + z[1]

    # calculate the y-error (residuals)
    y_err = y -p_y
     
    # create series of new test x-values to predict for
    p_x = np.arange(np.min(x),np.max(x)+1,1)

    # now calculate confidence intervals for new test x-series
    mean_x = np.mean(x)         # mean of x
    n = len(x)              # number of samples in origional fit
    t = 2.57                # appropriate t value (where n=9, two tailed 95%)
    s_err = np.sum(np.power(y_err,2))   # sum of the squares of the residuals
    
    # confidence interval on slope
    std_err = np.sqrt(
        (s_err/(n-2))/np.sum(np.power(x-mean_x,2))
    )
    
    z0_int = (z[0]-std_err,z[0]+std_err)

    print(z0_int)

    confs = t * np.sqrt((s_err/(n-2))*(1.0/n + (np.power((p_x-mean_x),2)/
                ((np.sum(np.power(x,2)))-n*(np.power(mean_x,2))))))

    # now predict y based on test x-values
    p_y = z[0]*p_x+z[1]
     
    # get lower and upper confidence limits based on predicted y and confidence intervals
    lower = p_y - abs(confs)
    upper = p_y + abs(confs)
    
    plt.subplot(n_plots,1,m)

    # set-up the plot
    # plt.axes().set_aspect('equal')
    plt.xlabel('Years')
    plt.ylabel('SST')
    title = "Time-series linear regression and confidence limits"\
    + "\nFit: slope = {}, intercept = {} ".format(round(z[0],3),round(z[1],3))\
    + "\nSlope 95% confidence interval: ({},{}) ".format(round(z0_int[0],3),round(z0_int[1],3))
    plt.title(title)
     
    # plot sample data

    plt.plot(x,y,'bo',label='Sample observations')
    # plot line of best fit
    plt.plot(c_x,c_y,'r-',label='Regression line')

    # plot confidence limits
    plt.plot(p_x,lower,'b--',label='Lower confidence limit (95%)')
    plt.plot(p_x,upper,'b--',label='Upper confidence limit (95%)')
     


    # set coordinate limits
    plt.xlim(years[0],years[1])
    plt.ylim(10,30)
     
    # configure legend
    plt.legend(loc=0)
    leg = plt.gca().get_legend()
    ltext = leg.get_texts()
    plt.setp(ltext, fontsize=10)
    

    if counts:
        m += 1
        plt.subplot(n_plots,1,m)
        plt.scatter(x,counts)
        plt.ylabel('Counts')

    if residuals:
        m += 1
        plt.subplot(n_plots,1,m)
        plt.scatter(x,y_err)
        plt.ylabel('Residuals')

    # show the plot
    plt.show()

if __name__ == '__main__':
    # years = (1865,1940)
    # name = '739_1853'

    # names = ('1504_1221', '494_1813',  '739_1853')
    # for name in names:
    #     hmonth=12
    #     avg_ssts,counts,yrs = yearly_data_time_series(name,years,hmonth=hmonth)
    #     yrs = np.array(list(map(int,yrs)))
    #     avg_ssts = np.array(list(map(float,avg_ssts)))
        
    #     slope, intercept, r_value, p_value, std_err = stats.linregress(
    #         yrs,avg_ssts)
    #     print(
    #         "\nslope",slope, 
    #         "\nintercept",intercept,
    #         "\nr_value**2",r_value**2,
    #         "\np_value",p_value, 
    #         "\nstd_err",std_err)
    #     # for result in group_series_in_decades(name,years,hmonth):
    #     #     print(result)

    years = (1920,1940)

    hmonth=12
    
    name = '739_1853'
    names = ('1504_1221', '494_1813',  '739_1853')
    for name in names:
        avg_ssts,counts,yrs = yearly_data_time_series(name,years,hmonth=hmonth)
        yrs = np.array(list(map(int,yrs)))
        avg_ssts = np.array(list(map(float,avg_ssts)))

        print('size: ',len(avg_ssts))
        regressions(yrs,avg_ssts,years,counts=counts,residuals=True)

    # plt.show)
    # avg_ssts,counts,dec_labels,dec_indices = zip(*group_series_in_decades(name,years,hmonth))
    
    
    # yrs = np.array(list(map(int,dec_indices)))
    # avg_ssts = np.array(list(map(float,avg_ssts)))

    # decs = [yrs[0],yrs[-1]]
    # print('size: ',len(avg_ssts))
    # regressions(yrs,avg_ssts,decs)
