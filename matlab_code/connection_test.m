clear all

%global d = 3;

f = @connection_bipartite_d;
%f = @connection_fully;

for i = 1:10
    j = randi(10,1,1);
    
    k = f(i,j);
    if k
        fprintf("conectados (%d) (%d)\n",i,j)
    else
        fprintf("não conectados (%d) (%d)\n",i,j)
    end
end