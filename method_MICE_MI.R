pool_parameters <- function(param_estimates_list, n) {
    # Initialize list to store results for each parameter
    pooled_results <- list()
    
    # Get parameter names (A0, A1, A2)
    param_names <- param_estimates_list[[1]]$parameter
    
    # Loop through each parameter (A0, A1, A2)
    for(param_idx in 1:length(param_names)) {
        param_name <- param_names[param_idx]
        
        # Extract betas (estimates) and SEs for this parameter across all imputations
        betas <- sapply(param_estimates_list, function(x) x[param_idx, "estimate"])
        ses <- sapply(param_estimates_list, function(x) x[param_idx, "se"])

        unw_betas <- sapply(param_estimates_list, function(x) x[param_idx, "unweighted_estimate"])
        unw_ses <- sapply(param_estimates_list, function(x) x[param_idx, "unweighted_se"])
        
        # Pool using Rubin's rules
        pooled <- pool.scalar(Q = betas, U = ses^2, n = n, k = length(param_estimates_list))
        pooled_unw <- pool.scalar(Q = unw_betas, U = unw_ses^2, n = n, k = length(param_estimates_list))
        
        # Create individual param_estimates for this parameter
        param_estimates <- data.frame(
            method = param_estimates_list[[1]]$method[param_idx],
            parameter = param_name,
            true_value = param_estimates_list[[1]]$true_value[param_idx],
            estimate = pooled$qbar,
            se = sqrt(pooled$t),
            unweighted_estimate = pooled_unw$qbar,
            unweighted_se = sqrt(pooled_unw$t)
        )
        
        # Store in results list
        pooled_results[[param_name]] <- param_estimates
    }
    
    return(pooled_results)
}


perform_MICE <- function(df, sample_size, rho)
{
    #print("Starting multiple imputation...")
    #print(head(df, 50))
    censoringA1 <- df$censoringA1
    censoringA2 <- df$censoringA2
    df <- df[, !colnames(df) %in% c("censoringA1", "censoringA2")]

    methods <- make.method(df)

    # skip constant variable Y0
    methods["Y0"] <- ""  

    methods["Y2"] <- "logreg"  
    methods["Y1"] <- "logreg"
    methods["Y3"] <- "logreg"
    methods["A0"] <- "logreg"
    methods["A1"] <- "logreg"

    imp <- mice(df, m=5, method=methods, printFlag=FALSE)

    compl <- complete(imp, 1)

    param_estimates_list <- list()
    violations_list <- list()

    for(imp_num in 1:imp$m) {
        completed_data <- complete(imp, imp_num)

        # for(col in colnames(completed_data)) {
        #     cat(sprintf("Missingness in %s: %d\n", col, sum(is.na(completed_data[[col]]))))
        # }

        # print("DF data before A1, A2:")
        # cat("A1 value counts:\n")
        # print(table(df$A1, useNA = "ifany"))
        # cat("A2 value counts:\n")
        # print(table(df$A2, useNA = "ifany"))

        # assign back structural missingness
        completed_data$A1[censoringA1 == TRUE] <- NA
        completed_data$A2[censoringA2 == TRUE] <- NA

        # print("Completed data after A1, A2:")
        # cat("A1 value counts:\n")
        # print(table(completed_data$A1, useNA = "ifany"))
        # cat("A2 value counts:\n")
        # print(table(completed_data$A2, useNA = "ifany"))
        
        results <-model_data(completed_data, rho)

        modelled_data <- results$param_estimates
        violations_list <- results$violations


        # print("modelled data:")
        # print(modelled_data)

        sim_results_df <- data.frame(
            method = character(3),
            parameter = character(3),
            true_value = numeric(3),
            estimate = numeric(3),
            se = numeric(3),
            unweighted_estimate = numeric(3),
            unweighted_se = numeric(3)
        )
        for(j in 1:3) {
            idx <- 6 + j  # 7, 8, 9
            param_name <- paste0("A", j-1)
            sim_results_df[j, ] <- list(
                method = "weighted",
                parameter = param_name,
                true_value = modelled_data[idx, 1],
                estimate = modelled_data[idx, 4],
                se = modelled_data[idx, 5],
                unweighted_estimate = modelled_data[idx, 2],
                unweighted_se = modelled_data[idx, 3]
            )
        }
        param_estimates_list[[imp_num]] <- sim_results_df
    }

    # remove any null results from failed models
    param_estimates_list <- param_estimates_list[!sapply(param_estimates_list, is.null)]

    pooled_results <- pool_parameters(param_estimates_list, n = sample_size)
    #print("Parameter estimates pooled:")
    #print(pooled_results)

    #return(pooled_results)
    return(list(
        param_estimates = pooled_results,
        violations = violations_list
    ))
}
