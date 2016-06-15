command script import command.py
breakpoint set --name sort
run 1 6 3 9 0
record --output=testData/integrationTestOutputGood.json
c
run 1 6 5 9 0
record --output=testData/integrationTestOutputBad.json
c
script import os; os._exit(1)
