
import pyvisa as pv 
import matplotlib.pyplot as plt
import time

def format_trace4(string_result):
    '''
    expected format: X.XXXXXXEXX, 0.000000E00\n
    '''
    lines = [x.strip() for x in string_result.split('\n')]
    points = [(line.split(',')[0].strip()) for line in lines]
    floats = []
    for p in points:
        try: 
            floats.append(float(p))
        except ValueError:
            print('Not a float: ' + str(p))
    return floats

def send_command(na, cmd_list):
    cmd = ';'.join(cmd_list)
    print('Sending command: ' + cmd)
    res = na.query(cmd)
    print('Response Received')
    return res 
    

def plot_trace(xs, ys, position, title='Axion Cavity Resonance Scanner', fig=None, ax=None):
    if(ax is None):
        fig, ax = plt.subplots(1,1)
    ax.plot(xs, ys, label='Positioner at ' + str(position) + ' mm')
    ax.set_xlabel('Frequency (Hz)')
    ax.set_ylabel('Response')
    ax.set_title(title)
    ax.legend()
    time0 = time.time()
    fig.savefig(str(time0)+'.png')
    return fig, ax

def print_trace(na, position=None, fig=None, ax=None):
    trace_format = 'FORM4'
    write_cmd = 'OUTPFORM'
    str_res = send_command(na, [trace_format, write_cmd])
    response = format_trace4(str_res)

    lim_cmd = 'OUTPLIML'
    str_res = send_command(na, [lim_cmd])
    freqs = format_trace4(str_res)

    fig, ax = plot_trace(freqs, response, position,fig=fig, ax=ax)
    return fig, ax 

def initialize_device():
    rm = pv.ResourceManager()
    resources = rm.list_resources()
    na_name = resources[0]
    device = rm.open_resource(na_name)
    return device 

def main():
    
    device = initialize_device()
    fig, ax = print_trace(device)
    fig.show()
    return 

if __name__ == '__main__':
    main()