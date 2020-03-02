function rho_end = scaledSISExact_allTopologies(vec_lambda, vec_mu, vec_gamma, vec_N, f_connection)

    global NumUsu;
    
    %% Real calculates, using the formulate exact
    % Lambda represents the exogenous infection factor
    qtd_lambda  = length(vec_lambda);
    % healing factor
    qtd_mu      = length(vec_mu);
    % Gamma represents the endogenous infection factor
    qtd_gamma   = length(vec_gamma);
    %  N - represents the total susceptibles (individuals)
    qtd_N       = length(vec_N);
    
    rho = -1 * ones(qtd_lambda, qtd_mu, qtd_gamma, qtd_N);
    
    %% Calculates all \tilde{\pi} - exact values
    ilambda = 0;
    for sup_lambda = vec_lambda
        ilambda = ilambda +1;
        imu = 0;
        for mu = vec_mu
            imu = imu + 1;
            igamma=0;
            for gamma = vec_gamma
                igamma=igamma+1;
                iN=0;
                for N=vec_N %% ((sup_lambda-inf_lambda)/qtd_lambda):sup_lambda
                    iN=iN+1;
                    % Define lambda (exogenous infection) in function of N
                    lambda = sup_lambda/N;
                    % Connectivity Matrix to completed graph
                    A=ones(N,N);
                    for i=1:N
                        for j=1:N
                            if i == j
                                A(i,i)=0;
                            else
                                NumUsu = N;
                                A(i,j)=f_connection(i,j);
                            end
                            
                        end
                    end
                    % x is a vector representing the states, x(j) is the j-esimo element.
                    % x=zeros(N,1);

                    % \pi is a vector representing the constant of equilibrium of
                    % transition states matrix Q and the probability of the states
                    % Initializing \tilde{\pi}
                    tilde_pi      = zeros(N+1,1);
                    iota          = zeros(1,N+1);
                   
                    % To contamitations 0..N
                    for i=0:N
                        if (i>0)
                            % generete all permutations
                            C = nchoosek(1:N,i);
                            nc = size(C,1);
                            allperm = accumarray([repmat((1:nc)',i,1),C(:)],1);
                            iota(1,i+1) = nc;
                            
                            % To all permutations 1..nc
                            for j=1:nc
                                % select next permutation
                                x = allperm(j,:)';
                                % my_exponent1 is number of contamined edges
                                my_exponent1=((x'*A*x)/2);
                                tilde_pi(i+1) = tilde_pi(i+1) + ((lambda/mu)^i * (gamma^my_exponent1));
                            end
                        else
                            % zero contaminads 
                            % \tilde{\pi}_0 = (\frac{\lambda}{\mu})^0 \gamma^0 = 1
                            tilde_pi(i+1) = 1;
                        end
                    end
                    
                    fprintf("N=%d lamb=%4.1f mu=%3.1f gamma=%4.2f",N, lambda, mu, gamma)
                    %fprintf("N=%d",N)
                    for ch = 1:length(tilde_pi)
                        fprintf("\t \\tilde{\\pi_%d}=%.3f",ch, tilde_pi(ch))
                    end
                    fprintf("\n")
                    
                    % single values
                    spi{iN}.N     = N;
                    spi{iN}.gamma = gamma;
                    spi{iN}.lambda= lambda;
                    spi{iN}.lambda= mu;
                    % vector values
                    spi{iN}.iota  = iota;
                    spi{iN}.pi    = tilde_pi;
                    %fprintf("Finalizado N=%2d \t lambda=%6.2f \t gamma=%5.3f \t mu=%5.3f\n", N, sup_lambda, gamma, mu);
                end
                
                iN=0;
                % for all N
                for N=vec_N %
                    iN=iN+1;
                    tilde_pi = spi{iN}.pi;
                    mean_infected = [0:N]*(tilde_pi/sum(tilde_pi));
                    prob_infected = mean_infected/iN;
                    rho(ilambda, imu, igamma, iN) = prob_infected;
                end
            end  % vec_gamma
        end % vec_mu
    end % vec_lambda
    
    rho_end = rho;

end