import matplotlib.pyplot as plot
from mpl_toolkits.mplot3d import axes3d
import re
import subprocess
import copy
import sqlite3

db = sqlite3.connect('run.db')
curs = db.cursor()

#nbody = pbs.Command("/home/colin/Dropbox/Repos/milkywayathome_client/bin/milkyway_nbody")

"""
def run(lua, hist, params):
    command = ' '.join(map(str, params))
    output = nbody('-h %s' % hist, '-f %s' % lua, '-e 1', command, _err_to_out=True)#_ok_code=12)
    print 'output = %s' % output
    output = re.search('<search_likelihood>([-0-9.-]+)</search_likelihood>', output)
    return output.group(1)
"""
ideal = [2, 2, 4, 0.5, 10, .20,]
var_name = ['Reverse Evolve Time', 'Forward Evolve Time', 'Dark Matter Radius','Light Matter Radius Ratio', 'Dark Matter Mass', 'Light Matter Mass Ratio']

def query_db(params, seed =1):
    sql = 'select fitness from fitness where p1 = %f and p2 = %f and p3 = %f and p4 = %f and p5 = %f and p6 = %f and seed = %f' % (params[0], params[1], params[2], params[3], params[4], params[5], seed)
    curs.execute(sql)
    output = curs.fetchall()
    if len(output) == 1:
        return output[0][0]
    if len(output) < 1:
        return None
    return output
    
def query_db_variable(variable):
    use = set(range(6))
    use.remove(variable)
    sql = 'select fitness, p%s, seed from fitness where ' % (variable+1)
    sql += ' and '.join('p%s = %s' % (i+1, ideal[i]) for i in use)
    curs.execute(sql)
    output = curs.fetchall()
    return output
    
def query_db_variables(v1, v2):
    use = set(range(6))
    use.remove(v1)
    use.remove(v2)
    sql = 'select fitness, p%s, p%s, seed from fitness where ' % (v1+1, v2+1)
    sql += ' and '.join('p%s = %s' % (i+1, ideal[i]) for i in use)
    curs.execute(sql)
    output = curs.fetchall()
    return output
    
def store_db(params, fitness, seed=1):
    curs.execute('INSERT INTO fitness Values (%s, %s, %s, %s, %s, %s, %s, %s)' % (seed, params[0], params[1], params[2], params[3], params[4], params[5], fitness))
    db.commit()


def run(lua, hist, params, seed = 1):
    print 'Case %s' % params
    found = query_db(params, seed = seed)
    if found == None:
        print 'Running %s' % params
        command = ' '.join(map(str, params))
        output = ' -h %s -f %s -e %s ' % (hist, lua, seed)
        binary = "/home/colin/Dropbox/Repos/milkywayathome_client/bin/milkyway_nbody"
        output = subprocess.check_output(binary + output + command, shell=True, stderr=subprocess.STDOUT)
        output = re.search('<search_likelihood>([-0-9.]+)</search_likelihood>', output)
        fitness = output.group(1)
        store_db(params, fitness, seed = seed)
        print 'Done with %s' % params
        return fitness
    print 'Found %s' % (params)
    return found
    

def Generate_points():
    best = [2, 2, 4, 0.5, 10, .20,]
    fidelity = 0.001
    for i in range(len(best)):
        graph = []
        for diff in [x * fidelity * best[i]  for x in range(-100, 110)]:
            new = copy.copy(best)
            new[i] += diff
            graph.append(run("plum_slice_EMD.lua", "plum_slice_EMD.hist", new))
        print 'Creating Graph fig%s_%s' % (i, fidelity)
        plot.figure()
        plot.plot([x * fidelity * best[i]  for x in range(-100, 110)], graph, '.')
        plot.title('Variable %s' % i)
        plot.xlabel('Difference')
        plot.ylabel('Fittness w/ EMD')
        plot.savefig('fig%s_%s.png' % (i, fidelity) )
        print 'Done'
        
def Generate_point(x, variable, seed):
    new = copy.copy(ideal)
    new[variable] = x
    run("plum_slice_EMD.lua", "plum_slice_EMD.hist", new, seed = seed)
    
def Generate_points(x, v1, y, v2):
    new = copy.copy(ideal)
    new[v1] = x
    new[v2] = y
    run("plum_slice_EMD.lua", "plum_slice_EMD.hist", new)
        
        
def Generate_range(start, stop, step, variable, seed = 1):
    i = start
    while i < stop:
        Generate_point(i, variable, seed = seed)
        i += step
        
def Generate_ranges(start, stop, step, v1, v2):
    i = start
    while i < stop:
        j = start
        while j < stop:
            Generate_points(i, v1, j, v2)
            j += step
        i += step
        
        
def Print_graphs(start= 0, stop = 15, symbol = '.'):
    for i in range(6):  
        points = query_db_variable(i)
        x = [j[1] for j in points if (j[1] > start and j[1] < stop)]
        y = [j[0] for j in points if (j[1] > start and j[1] < stop)]
        points = zip(x,y)
        points = sorted(points, key=lambda k:k[0])
        x = [k[0] for k in points]
        y = [k[1] for k in points]
        
        print 'Creating Graph fig_%s_start_%s_stop_%s' % (i, start, stop)
        plot.figure()
        plot.plot(x, y,symbol)
        plot.title(var_name[i])
        plot.xlabel('Value')
        plot.ylabel('Fittness w/ EMD')
        plot.savefig('fig_%s_start_%s_stop_%s.png' % (i, start, stop) )
        print 'Done'
        
def Print_graphs_3d(start = 0, stop = 15):
    for i in range(6):
        for j in range(i):
            points = query_db_variables(i, j)
            x = [p[1] for p in points if (p[1] > start and p[1] < stop)]
            y = [p[2] for p in points if (p[1] > start and p[1] < stop)]
            z = [p[0] for p in points if (p[1] > start and p[1] < stop)]
            print 'Creating Graph fig2d_%s_%s_start_%s_stop_%s' % (i, j, start, stop)
            fig = plot.figure()
            ax = fig.add_subplot(111, projection='3d')
            ax.scatter(x,y,z)
            ax.set_xlabel(var_name[i])
            ax.set_ylabel(var_name[j])
            ax.set_zlabel('Z Axis')
            plot.title(var_name[i] +', ' + var_name[j])
            
            plot.savefig('fig2d_%s_%s_start_%s_stop_%s.png' % (i, j, start, stop))
            print 'Done'
        
        

if __name__ == "__main__":
    print 'Starting db setup'
    curs.execute('CREATE TABLE IF NOT EXISTS fitness (seed INTEGER, p1 REAL, p2 REAL, p3 REAL, p4 REAL, p5 REAL, p6 REAL, fitness REAL)')
    db.commit()
    print 'running test cases'
    #Print_graphs_3d()
    #Generate_ranges(2.0,3.0, 0.5, 0, 1)
    #Print_graphs_3d()
    
    Generate_range(4.0, 6.0, 0.1, 4, seed=2)
    
    print 'done'
    print 'Making graphs'
    Print_graphs()
    Print_graphs(start=0.2, stop = 0.4)
    Print_graphs(start=0.1, stop = 0.3)
    Print_graphs(start=9.0, stop = 11)
    Print_graphs(start=4,stop = 16, symbol = '')
    Print_graphs(start=3, stop = 5)
    print 'Done'
