with open(__file__+'.log','w') as csv:
    csv.write('tool,date,pyt,workspace,map,user\n')
    with open('WIPTools.pyt.log') as log:
        for line in log.readlines():
            if '.pyt' in line:
                l = line \
                    .replace(' run started at ',',') \
                    .replace(' from ',',') \
                    .replace(' using workspace ',',') \
                    .replace(' and map ',',') \
                    .replace(' by ',',') 
                csv.write(l)
            
