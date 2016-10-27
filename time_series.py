from analysis import *
import numpy as np
import pandas as pd
import scipy.stats as stats

class TimeSeriesOLS:
    """Organizing calculations and tests on time series regression."""
    def __init__(self,series,times,years=None):
        self.series = np.array(series).astype(np.float)
        self.times = np.array(times).astype(np.int)
        self.m,self.b,self.r_value,self.p_value,self.std_err = self.ols()
        if years:
            self.years = years
        self.mean = np.mean(self.series)
        self.sd = np.std(self.series)
        self.ratio = pow(self.sd,2.)/len(self.series)

    def ols(self):
        """Do OLS on times series, get pars and stats."""
        m,b,r_value,p_value,std_err = stats.linregress(self.times,self.series)
        return m,b,r_value,p_value,std_err 

    def residuals(self):
        """Calculate residuals of OLS fit."""
        return self.series-(self.m*self.times+self.b)

    def f_test(self,test_series):
        """F-test of equal variances."""
        # print(stats.bartlett(self.series,test_series))
        # return stats.f.sf(F, df1, df2)
        return stats.levene(self.series,test_series)

    def process_years(self,years):
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

    # Temporary ------------
    def check_res_sum(self):
        """Residuals should sum to zero when OLS done correctly."""
        return np.sum(self.residuals())

    def check_est_exogeneity(self):
        return np.abs(np.sum(self.times*self.residuals()))

class BoxStatTests:
    """Compare statistics between different boxes.  Start with a given box, then
    test whether a different box's data can be merged with the first box.  If
    the second box passes all tests, merge it, otherwise discard.
    """
    def __init__(self,series,years):
        self.series = np.array(series).astype(np.float)
        if years:
            self.years = years
            self.yrs = range(years[0],years[1]+1)
        self.mean = np.mean(self.series)
        self.sd = np.std(self.series)
        self.ratio = pow(self.sd,2.)/len(self.series)

    def equal_means_test(self,test_series,alpha=.05):
        """Equal means test, assumes two populations have equal means.
        """
        # simple stats of test series
        test_series = np.array(test_series)
        test_mean = np.mean(test_series)
        test_sd = np.std(test_series)
        # difference of means
        diff_means = self.mean - test_mean 
        # ratio of variance to sample size of the test series
        test_ratio = pow(test_sd,2.)/len(test_series)
        # standard error
        std_err = pow(self.ratio+test_ratio,.5)
        # dof eq 
        # from http://stattrek.com/hypothesis-test/difference-in-means.aspx?Tutorial=AP
        dof = pow(std_err,4.)/(pow(self.ratio,2.)/(len(self.series)-1.)
            + pow(test_ratio,2.)/(len(test_series)-1.))
        dof = round(dof,0)
        # test statistic
        t = diff_means/std_err
        # t-distribution 95% confidence interval upper bound (symmetric)
        conf_bnd = stats.t.ppf(1.-alpha/2., dof)
        return np.abs(t)<conf_bnd


def corr_radius_boxes(center,radius,years,hmonth=None,pentads=None,alpha=0.05):
    # Check input ok, no redundant time periods
    if isinstance(years,(int,str)):
        years = (years,years)
    periods = [hmonth,pentads]
    period_chk = 0
    for period in periods:
        if period:
            period_chk += 1
        if period_chk != 1:
            return "corr_radius_boxes: no good, check your time periods."
    if hmonth:
        pentads = conv_hmth_pentad(hmonth)
    # SST data for center box
    ssts = box_sst_data(center,years,pentads=pentads)[2]
    # Comparison object for center box 
    x = BoxStatTests(ssts,years)
    names = boxes_within_radius(center,radius)
    # Test surrounding boxes are similar (equal means) to center box
    keep = list()
    throw = list()
    for name in names:
        ssts = box_sst_data(name,years,pentads=pentads)[2]
        if len(ssts) > 1:
            test = x.equal_means_test(ssts,alpha=alpha)
            if test == True:
                keep.append(name)
            elif test == False:
                throw.append(name)
    ratio = len(keep)/(len(keep)+len(throw))
    return keep,throw,ratio

def radius_tolerance(center,years,hmonth=None,tolerance=0.67):
    """Given a center box, the time period of the data, and the desired 
    percentage of boxes that pass a test, find the radius that yields the given
    tolerance.

    Do binary search on the radius with criteria on tolerance.  If the max and 
    min of the binary search interval is small, or if the number of iterations
    is large, break and return radius.
    """
    if isinstance(years,(int,str)):
        years = (years,years)

    mn = 0.    
    mx = 1000.
    radius = 100.
    interval = [mn,mx]
    # binary search radius by tolerance
    search = True
    iteration = 0
    keep = list()
    throw = list()
    while search == True:
        iteration += 1
        try:
            keep,throw,ratio = corr_radius_boxes(center,radius,years,hmonth=hmonth)
            if ratio > tolerance:
                interval[0] = radius
            elif ratio < tolerance:
                interval[1] = radius
        except:
            ratio = 0.
            interval[0] = radius
        diff = interval[1] - interval[0]
        if  diff < 2. or iteration > 25. or (tolerance-.01 < ratio < tolerance):
            break 
        radius = interval[0] + diff/2.
    return radius,ratio,keep,throw

def make_timeseries(center,years,hmonth=None,pentads=None):
    """NOT FINISHED, NEED TO FINISH INPUTS AND CHECK A RUN!!!
    Created a time series starting with a central box, then adding data from
    similar boxes surrounding the center box.  Relies on function
    radius_tolerance().  Also, similar boxes determined by the difference of
    means statistical test.
    """

    all_keeps = list()
    
    for yr in range(years[0],years[1]+1):
        # print(yr)
        # keep,throw = corr_radius_boxes(name,radius,years,hmonth=hmonth)
        radius,ratio,keep,throw = radius_tolerance(center,yr,hmonth=hmonth,tolerance=0.67)
        # if ratio > 0.:
        keep.extend(throw)
        # print(radius,ratio,keep,throw)
        all_keeps.append((yr,keep))

    series = list()
    times = list()
    for (yr,keep) in all_keeps:
        print(yr)
        sys.stdout.flush()
        try:
            avg_ssts,counts,yrs = mean_sst_by_year(keep,(yr,yr),pentads=pentads)
            if avg_ssts:
                series.append(avg_ssts[0])
                times.append(int(yrs[0]))
        except:
            pass
    timeseries = list(zip(times,series))
    return timeseries

if __name__ == '__main__':
    years = (1900,1902)
    name = '739_1853'
    hmonth = 1
    pentads = conv_hmth_pentad(hmonth)

    timeseries = make_timeseries(name,years,hmonth=hmonth)
    file = 'mid_atlantic_1850_1940.txt'
    with open(file,'a') as out_file:
        for ts in timeseries:
            out_file.write("     ".join(map(str,ts))+'\n')
    # pickle_list(timeseries,file=file)
    # print(load_pickle_list(file=file))






    # class StatBoxTests:
    # """Compare statistics between different boxes.  Start with a given box, then
    # test whether a different box's data can be merged with the first box.  If
    # the second box passes all tests, merge it, otherwise discard.
    # """
    # def __init__(self,name,years):
    #     self.name = name
    #     self.merge = [name]
    #     self.years = years
    #     self.data = self.sst_data(self.name,self.years)
    #     self.n = len(self.data)
    #     # self.mean,self.std = self.simple_stats(self.data)

    # def sst_data(self,names,years):
    #     if isinstance(names,str):
    #         names = [names]
    #     date_min,date_max = self.process_years(years)
    #     sql = "select name, sst "\
    #     + "from obsdata "\
    #     + "where name in ('{}') ".format("','".join(names))\
    #     + "and date between '{}' and '{}' ".format(date_min,date_max)\
    #     + ";"
    #     try:
    #         ssts = list(db_box.execute_sql(sql))
    #     except:
    #         ssts = list()
    #     # sort results into dictionary
    #     d_ssts = dict()
    #     for (key,value) in ssts:
    #         d_ssts.setdefault(key,[]).append(value)
    #     # convert to numpy arrays
    #     for key in d_ssts:
    #         d_ssts[key] = np.array(d_ssts[key])
    #     return d_ssts

    # def simple_stats(self,data):
    #     """Return simple statistics on data array."""
    #     return np.mean(data),np.std(data,ddof=1)

    # def process_years(self,years):
    #     """Utility to handle different inputs for years and generate title of 
    #     plot.
    #     """
    #     if isinstance(years,(list,tuple)):
    #         years = tuple(sorted(years))
    #     else:
    #         years = (years,years)
    #     date_min = str(years[0])+'-01-01'
    #     date_max = str(years[1])+'-12-31'
    #     return date_min,date_max

    # def perform_tests(self,test_sample_names):
    #     """Perform tests to check if two data sets are sampled from the same 
    #     distribution.  If they are, merge them.
    #     """
    #     # set up test set data
    #     self.test = test_sample_names
    #     self.test_data = self.sst_data(self.test,self.years)
    #     # self.test_mean,self.test_std = self.simple_stats(self.test_data)

    #     # perform sample tests
    #     print('variance test')
    #     pass_test = False
    #     for t,test in zip(self.test,self.equal_variances()):
    #         print(t,test)
    #     print()
    #     print('mean test')
    #     for t,test in zip(self.test,self.equal_means()):
    #         print(t,test)

    #     # self.equal_means()
    #     #         pass_test = True
    #     return pass_test

    # def equal_variances(self):
    #     """Testing variances between two samples is equal using Levene test. """
    #     pvalues = list()
    #     for key in self.test_data:
    #         pvalues.append(stats.levene(self.data[self.name],self.test_data[key])[1])
    #     return pvalues

    # def equal_means(self):
    #     """Test of null hypothesis that two samples have identical mean."""
    #     # print(self.mean,self.test_mean)
    #     pvalues = list()
    #     for key in self.test_data:
    #         pvalues.append(stats.ttest_ind(self.data[self.name],self.test_data[key])[1])
    #     return pvalues

    # def means_t_test(self,test_name):
    #     """Test statistic of difference of means for samples of different 
    #     size.
    #     """
    #     # test data simple stats
    #     self.test_name = test_name
    #     self.test_data = self.sst_data(self.test_name,self.years)
    #     self.test_mean = np.mean(self.test_data[self.test_name])
    #     self.test_std = np.std(self.test_data[self.test_name])
        
    #     # main data set simple statistics
    #     self.mean = np.mean(self.data[self.name])
    #     self.std = np.std(self.data[self.name],ddof=1)


    #     print(self.data)
    #     print(self.mean,self.std,len(self.data[self.name]))
    #     print()


    #     print(self.test_data)
    #     print(self.test_mean,self.test_std,len(self.test_data[self.test_name]))
    #     print()
