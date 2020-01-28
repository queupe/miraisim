clear all


lambda_vec = [1500];
mu_vec     =    [17.9593, 18.1603, 18.0462, 17.4592, ...
                 154.8883, 44.7099, 21.4111, 15.7172, ...
                 122.9877, 43.5209, 20.9333, 2.8819];
gamma_vec  =    [1.0071 , 1.0092 , 1.0148 , 1.0383 , ...
                 1.0262  , 1.0262 , 1.0148 , 1.0071 , ...
                 1.0061  , 1.0148 , 1.0148 , 1.0171];             


vec_N      = [1, 5, 10, 15];

f = @connection_fully;

aux1 = scaledSISExact_allTopologies(lambda_vec, mu_vec, gamma_vec, vec_N, f);