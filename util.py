from pymms.sdc import selections as sel
from pymms.sdc import mrmms_sdc_api as api
import cdflib
import datetime as dt
import numpy as np
from matplotlib import pyplot as plt
from matplotlib import dates as mdates
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import pathlib
outdir = None #pathlib.Path('/Users/argall/Desktop/')


# cdfepoch requires datetimes to be broken down into 9-element lists
def datetime_to_list(t):
    return [t.year, t.month, t.day,
            t.hour, t.minute, t.second,
            int(t.microsecond // 1e3),
            int(t.microsecond % 1e3),
            0]

def tt2000_range(cdf, t_vname, start_date, end_date):

    # Create lists
    tstart = datetime_to_list(start_date)
    tend = datetime_to_list(end_date)

    # Convert to TT2000
    tstart = cdflib.cdfepoch.compute(tstart)
    tend = cdflib.cdfepoch.compute(tend)

    # Find the time range
    return cdf.epochrange(epoch=t_vname, starttime=tstart, endtime=tend)


def from_cdflib(files, varname, start_date, end_date):

    global cdf_vars
    global file_vars

    if isinstance(files, str):
        files = [files]
    tstart = datetime_to_list(start_date)
    tend = datetime_to_list(end_date)

    # Extract metadata
    cdf_vars = {}
    for file in files:
        file_vars = {}
        cdf = cdflib.CDF(file)

        try:
            data = cdflib_readvar(cdf, varname, tstart, tend)
        except:
            cdf.close()
            raise

        cdf.close()

    return data


def cdflib_readvar(cdf, varname, tstart, tend):
    global cdf_vars
    global file_vars

    # Data has already been read from this file
    if varname in file_vars:
        var = file_vars[varname]
    else:
        time_types = ('CDF_EPOCH', 'CDF_EPOCH16', 'CDF_TIME_TT2000')
        varinq = cdf.varinq(varname)

        # Convert epochs to datetimes
        data = cdf.varget(variable=varname, starttime=tstart, endtime=tend)
        if varinq['Data_Type_Description'] in time_types:
            data = cdflib.cdfepoch().to_datetime(data)

        # If the variable has been read from a different file, append
        if (varname in cdf_vars) and varinq['Rec_Vary']:
            d0 = cdf_vars[varname]
            data = np.append(d0['data'], data, 0)

        # Create the variable
        var = {'name': varname,
               'data': data,
               'rec_vary': varinq['Rec_Vary'],
               'cdf_name': varinq['Variable'],
               'cdf_type': varinq['Data_Type_Description']
               }

        # List as read
        #  - Prevent infinite loop. Must save the variable in the registry
        #  so that variable attributes do not try to read the same variable
        #  again.
        cdf_vars[varname] = var
        file_vars[varname] = var

        # Read the metadata
        cdflib_attget(cdf, var, tstart, tend)

    return var


def cdflib_attget(cdf, var, tstart, tend):

    # Get variable attributes for given variable
    varatts = cdf.varattsget(var['cdf_name'])

    # Get names of all cdf variables
    cdf_varnames = cdf.cdf_info()['zVariables']

    # Follow pointers to retrieve data
    for attrname, attrvalue in varatts.items():
        var[attrname] = attrvalue
        if isinstance(attrvalue, str) and (attrvalue in cdf_varnames):
            var[attrvalue] = cdflib_readvar(cdf, attrvalue, tstart, tend)


def plot_1D(data, axes):
    # Plot the data
    lines = axes.plot(mdates.date2num(data[data['DEPEND_0']]['data']),
                      data['data'])
    
    try:
        axes.set_yscale(data['SCALETYP'])
    except KeyError:
        pass
    
    try:
        # Set the label for each line so that they can
        # be returned by Legend.get_legend_handles_labels()
        for line, label in zip(lines, data[data['LABL_PTR_1']]['data']):
            line.set_label(label)

        # Create the legend outside the right-most axes
        leg = axes.legend(bbox_to_anchor=(1.05, 1),
                          borderaxespad=0.0,
                          frameon=False,
                          handlelength=0,
                          handletextpad=0,
                          loc='upper left')

        # Color the text the same as the lines
        for line, text in zip(lines, leg.get_texts()):
            text.set_color(line.get_color())

    except KeyError:
        pass


def plot_2D(data, axes):
    # Convert time to seconds and reshape to 2D arrays
    x0 = mdates.date2num(data[data['DEPEND_0']]['data'])
    x1 = data[data['DEPEND_1']]['data']
    if x0.ndim == 1:
        x0 = np.repeat(x0[:, np.newaxis], data['data'].shape[1], axis=1)
    if x1.ndim == 1:
        x1 = np.repeat(x1[np.newaxis, :], data['data'].shape[0], axis=0)

    # Format the image
    y = data['data'][0:-1,0:-1]
    try:
        if data['SCALETYP'] == 'log':
            y = np.ma.log(y)
    except KeyError:
        pass

    # Create the image
    im = axes.pcolorfast(x0, x1, y, cmap='nipy_spectral')
    axes.images.append(im)
    
    try:
        axes.set_yscale(data[data['DEPEND_1']]['SCALETYP'])
    except KeyError:
        pass

    # Create a colorbar to the right of the image
    cbaxes = inset_axes(axes,
                        width='1%', height='100%', loc=4,
                        bbox_to_anchor=(0, 0, 1.05, 1),
                        bbox_transform=axes.transAxes,
                        borderpad=0)
    cb = plt.colorbar(im, cax=cbaxes, orientation='vertical')


def plot_burst_selections(sc, start_date, end_date,
                          figsize=(5.5, 7)):
    mode = 'srvy'
    level = 'l2'

    # FGM
    b_vname = '_'.join((sc, 'fgm', 'b', 'gse', mode, level))
    mms = api.MrMMS_SDC_API(sc, 'fgm', mode, level,
                            start_date=start_date, end_date=end_date)
    files = mms.download_files()
    files = api.sort_files(files)[0]

    fgm_data = from_cdflib(files, b_vname,
                           start_date, end_date)
    fgm_data[fgm_data['LABL_PTR_1']]['data'] = ['Bx', 'By', 'Bz', '|B|']
    
    # FPI DIS
    fpi_mode = 'fast'
    ni_vname = '_'.join((sc, 'dis', 'numberdensity', fpi_mode))
    espec_i_vname = '_'.join((sc, 'dis', 'energyspectr', 'omni', fpi_mode))
    mms = api.MrMMS_SDC_API(sc, 'fpi', fpi_mode, level,
                            optdesc='dis-moms',
                            start_date=start_date, end_date=end_date)
    files = mms.download_files()
    files = api.sort_files(files)[0]

    ni_data = from_cdflib(files, ni_vname,
                          start_date, end_date)
    especi_data = from_cdflib(files, espec_i_vname,
                              start_date, end_date)

    # FPI DES
    ne_vname = '_'.join((sc, 'des', 'numberdensity', fpi_mode))
    espec_e_vname = '_'.join((sc, 'des', 'energyspectr', 'omni', fpi_mode))
    mms = api.MrMMS_SDC_API(sc, 'fpi', fpi_mode, level,
                            optdesc='des-moms',
                            start_date=start_date, end_date=end_date)
    files = mms.download_files()
    files = api.sort_files(files)[0]
    ne_data = from_cdflib(files, ne_vname,
                          start_date, end_date)
    espece_data = from_cdflib(files, espec_e_vname,
                              start_date, end_date)


    # Grab selections
    abs_data = sel.selections('abs', start_date, end_date)
    sitl_data = sel.selections('sitl+back', start_date, end_date)
    gls_data = sel.selections('mp-dl-unh', start_date, end_date)

    # SITL data time series
    t_abs = []
    x_abs = []
    for selection in abs_data:
        t_abs.extend([selection.tstart, selection.tstart,
                      selection.tstop, selection.tstop])
        x_abs.extend([0, selection.fom, selection.fom, 0])
    if len(abs_data) == 0:
        t_abs = [start_date, end_date]
        x_abs = [0, 0]
    abs = {'data': x_abs,
           'DEPEND_0': 't',
           't': {'data': t_abs}}

    t_sitl = []
    x_sitl = []
    for selection in sitl_data:
        t_sitl.extend([selection.tstart, selection.tstart,
                       selection.tstop, selection.tstop])
        x_sitl.extend([0, selection.fom, selection.fom, 0])
    if len(sitl_data) == 0:
        t_sitl = [start_date, end_date]
        x_sitl = [0, 0]
    sitl = {'data': x_sitl,
            'DEPEND_0': 't',
            't': {'data': t_sitl}}

    t_gls = []
    x_gls = []
    for selection in gls_data:
        t_gls.extend([selection.tstart, selection.tstart,
                      selection.tstop, selection.tstop])
        x_gls.extend([0, selection.fom, selection.fom, 0])
    if len(gls_data) == 0:
        t_gls = [start_date, end_date]
        x_gls = [0, 0]
    gls = {'data': x_gls,
           'DEPEND_0': 't',
           't': {'data': t_gls}}

    # Setup plot
    nrows = 7
    ncols = 1
    fig, axes = plt.subplots(nrows=nrows, ncols=ncols,
                             figsize=figsize, squeeze=False)
    locator = mdates.AutoDateLocator()
    formatter = mdates.ConciseDateFormatter(locator)

    # Plot FGM
    plot_2D(especi_data, axes[0,0])
    axes[0,0].set_title(sc.upper())
    fig.axes[-1].set_label('DEF')
    axes[0,0].set_ylabel('$E_{ion}$\n(eV)')
    axes[0,0].set_xticks([])
    axes[0,0].set_xlabel('')

    plot_2D(espece_data, axes[1,0])
    fig.axes[-1].set_label('DEF\nLog_{10}(keV/(cm^2 s sr keV))')
    axes[1,0].set_ylabel('$E_{e-}$\n(eV)')
    axes[1,0].set_xticks([])
    axes[1,0].set_xlabel('')
    axes[1,0].set_title('')

    plot_1D(fgm_data, axes[2,0])
    axes[2,0].set_ylabel('B\n(nT)')
    axes[2,0].set_xticks([])
    axes[2,0].set_xlabel('')
    axes[2,0].set_title('')

    plot_1D(ni_data, axes[3,0])
    axes[3,0].set_ylabel('$N_{i}$\n($cm^{-3}$)')
    axes[3,0].set_xticks([])
    axes[3,0].set_xlabel('')
    axes[3,0].set_title('')

    plot_1D(abs, axes[4,0])
    axes[4,0].set_ylabel('ABS')
    axes[4,0].set_xticks([])
    axes[4,0].set_xlabel('')
    axes[4,0].set_title('')

    plot_1D(gls, axes[5,0])
    axes[5,0].set_ylabel('GLS')
    axes[5,0].set_ylim(0, 200)
    axes[5,0].set_xticks([])
    axes[5,0].set_xlabel('')
    axes[5,0].set_title('')

    plot_1D(sitl, axes[6,0])
    axes[6,0].set_ylabel('SITL')
    axes[6,0].set_title('')
    axes[6,0].xaxis.set_major_locator(locator)
    axes[6,0].xaxis.set_major_formatter(formatter)
    for tick in axes[6,0].get_xticklabels():
        tick.set_rotation(45)
    
    # Set a common time range
    plt.setp(axes, xlim=mdates.date2num([start_date, end_date]))
    plt.subplots_adjust(left=0.15, right=0.85, top=0.93)
    return fig, axes