clear all

save_file = true;

OUTPUT_FOLDER_PDF = '../Notes/approx_Claude/img/';

N     = [1:200];
N = 200;
gamma1_vec = [1.03, 1.06, 1.07, 1.08, 1.09, 1.15, 1.52];
%gamma1_vec = [1.03];
%gamma1 = 1.09;
mu1   = 1.0;
%lambda = 10 .* (N.^(-1));
lambda = 10;
%rho0 = zeros(1, length(N));4
rho_vec = 0:0.25:1;

rho0 = 0.0;
rho1 = 1.0;
T    = 200;

iter = 10;
rho_ans0 = zeros(N,iter);
rho_ans1 = zeros(N,iter);

print_one = true;


f = figure('visible','on');
hold on;

ylim([0, 1]);
xlim([1,T]);


    for gamma1 = gamma1_vec
        %for rho0 = rho_vec

            for n = 2:N
                rho_ans0(n, 1) = next_rho_v2(lambda/n, rho0, mu1, gamma1, n-1);
                rho_ans1(n, 1) = next_rho_v2(lambda/n, rho1, mu1, gamma1, n-1);
                
                for x = 1:iter
                    rho_ans0(n, x+1) = next_rho_v2(lambda/n, rho_ans0(n, x), mu1, gamma1, n-1);
                    rho_ans1(n, x+1) = next_rho_v2(lambda/n, rho_ans1(n, x), mu1, gamma1, n-1);
                    
                    if rho_ans0(n, x+1) < 0 %&& rho_ans1(n, x+1) > 0
                        print_one = false;
                    end
                    
                end
            end

            %for i = 1:iter
                %plot(1:N, rho2(:,i))
                %plot(1:N, rho_ans(:,2), 'DisplayName',sprintf('\\rho_0=%f',rho0))

                %if print_one
                    plot(1:N, rho_ans1(:,2), '--', 'DisplayName',sprintf('\\rho_1 \\gamma_0=%f',gamma1))
                %else
                    plot(1:N, rho_ans0(:,2), ':',  'DisplayName',sprintf('\\rho_0 \\gamma_0=%f',gamma1))
                %end
                hold on
            %end

        %end

    %X = 1:200;
    %Y = zeros(1,200);
    %    for i = 1:iter
    %        Y = 1.09 .^ (-1 .* ((X - 1) .* Y));
    %        plot(X, Y, 'DisplayName',sprintf('\\iter=%d',i))
    %    end


    end

    lgd = legend('FontSize',8,'Location','southeast', 'Orientation','vertical','AutoUpdate','off');


