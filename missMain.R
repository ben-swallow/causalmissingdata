library(tidyverse)
library(parallel)
library(foreach)
library(iterators)
library(doParallel)
library(reticulate)
library(rsimsum)
library(mice)
library(broom)
library(sandwich)

if (!require(sandwich)) {
  install.packages("sandwich")
  library(sandwich)
}

# install Python packages if needed
if (!py_module_available("pandas")) {
  py_install("pandas")
}
if (!py_module_available("numpy")) {
  py_install("numpy")
}
if (!py_module_available("sklearn")) {
  py_install("scikit-learn")
}
if (!py_module_available("miceforest")) {
  py_install("miceforest")
}
if (!py_module_available("itertools")) {
  py_install("itertools")
}

pandas <- import("pandas")
numpy <- import("numpy")
# PARAMETERS
# K: Number of visits minus one
# rhos: Parameters for confounding strength (5 scenarios)
# betas: Parameters for the causal effect of interest
# gammas: Parameters for treatment allocation
# thetas: Parameters for the confounding mechanism

setwd(file.path("C:/Users/the_o/Desktop/Dissertation/MissingnessSimulation/MissingnessSim"))
# r main path
eavePath <- file.path(getwd(), "python_missingness_extension")
# missingness python path
pythonPath <- file.path(getwd(), "python_missingness_extension")


source(file.path(eavePath, "script/results.R"))
source(file.path(pythonPath, "call_python.R"))
source(file.path(pythonPath, "factor_screening.R"))
source(file.path(pythonPath, "scenario.R"))
source(file.path(pythonPath, "print_scenarios.R"))
source(file.path(pythonPath, "create_scenarios.R"))
source(file.path(pythonPath, "MICE_MI.R"))


estimate_performance_parallel <- function(resultsDf, nsims, sample_size, missingnessMethod) {
  # Setup parallel processing
  num_cores <- detectCores() - 1
  cl <- makeCluster(num_cores) # outfile=""
  registerDoParallel(cl)
  
  # Export necessary variables to workers
  clusterExport(cl, c("scenario", "K", "eavePath", "demographics", "gammas", 
                     "thetas", "betas", "a_k_values", "rho", "fhat", "pythonPath"))
  
  # Load required libraries and functions on each worker
  clusterEvalQ(cl, {
    library(tidyverse)
    library(mice)
    library(broom)
    library(sandwich)
    source(file.path(eavePath, "script/aux_functions.R"))
    source(file.path(eavePath, "script/simulate_data.R"))
    source(file.path(eavePath, "script/results.R"))
    source(file.path(pythonPath, "call_python.R"))
    source(file.path(pythonPath, "MICE_MI.R"))
  })
  
  # Run simulations in parallel
  all_res <- foreach(i = 1:nsims, 
                        .packages = c("tidyverse"), 
                        .errorhandling = "pass") %dopar% {
    
    tryCatch({
      # Set rho for this iteration (avoid global assignment)
      rho <- scenario$rho
      
      # Run single simulation
      sim_results <- simulate_single_dataset(sample_size)
      
      # Process data locally (no global assignments)
      combined_data_local <- cbind(as.data.frame(sim_results$b), 
                                  as.data.frame(sim_results$a), 
                                  as.data.frame(sim_results$y))
      
      combined_data_local[] <- lapply(combined_data_local, function(x) {
        if(is.factor(x)) as.numeric(x) else x
      })
      
      if(missingnessMethod != "None") {
        # If missingness is enabled, call the Python function
        combined_data_local <- call_python(combined_data_local, scenario, missingnessMethod)
      }

      # Build results for this simulation
      sim_results_df <- data.frame(
        sim = integer(3),
        method = character(3),
        parameter = character(3),
        true_value = numeric(3),
        estimate = numeric(3),
        se = numeric(3),
        unweighted_estimate = numeric(3),
        unweighted_se = numeric(3)
      )
      violations_list <- list()

      if(missingnessMethod == "MI") {
        #print("Performing multiple imputation...")
        miceResults <- perform_MICE(combined_data_local, scenario$sample_size, scenario$rho)
        #print("Multiple imputation done")
        param_estimates <- miceResults$param_estimates
        violations_list <- miceResults$violations

        for(j in 1:3) {
          idx <- 1  # 1, 2, 3
          param_name <- paste0("A", j-1)  # "A0", "A1", "A2"
          sim_results_df[j, ] <- list(
            sim = i,
            method = "weighted",
            parameter = param_name,
            true_value = param_estimates[[param_name]]$true_value,
            estimate = param_estimates[[param_name]]$estimate,
            se = param_estimates[[param_name]]$se,
            unweighted_estimate = param_estimates[[param_name]]$unweighted_estimate,
            unweighted_se = param_estimates[[param_name]]$unweighted_se
          )
        }
        #print("sim_results done")
      }
      else {
        results <- tryCatch(
          model_data(combined_data_local, rho),
          error = function(e) {
            warning(paste("Error in model_data at simulation", i, ":", e$message))
            return(NULL)
          }
        )

        param_estimates <- results$param_estimates
        violations_list <- results$violations

        for(j in 1:3) {
          idx <- 6 + j  # 7, 8, 9
          param_name <- paste0("A", j-1)  # "A0", "A1", "A2"
          sim_results_df[j, ] <- list(
            sim = i,
            method = "weighted",
            parameter = param_name,
            true_value = param_estimates[idx, 1],
            estimate = param_estimates[idx, 4],
            se = param_estimates[idx, 5],
            unweighted_estimate = param_estimates[idx, 2],
            unweighted_se = param_estimates[idx, 3]
          )
        }
      }
      #return(sim_results_df)
      return(list(
          sim_results = sim_results_df,
          violations = violations_list
      ))
    }, error = function(e) {
      warning(paste("Error in simulation", i, ":", e$message))
      return(NULL)  # Will be removed by error handling
    })
  }
  
  # Clean up
  stopCluster(cl)

  all_results <- do.call(rbind, lapply(all_res, function(x) {
    if (!is.null(x) && !is.null(x$sim_results)) {
      return(x$sim_results)
    } else {
      return(NULL)
    }
  }))

  # Extract violations from each iteration
  all_violations <- lapply(all_res, function(x) {
    if (!is.null(x) && !is.null(x$violations)) {
      return(x$violations)
    } else {
      return(NULL)
    }
  })

  # Check if all_results is valid (not NULL and has rows)
  if (is.null(all_results) || nrow(all_results) == 0) {
    warning("All simulations failed for this scenario:")
    print(paste("Mechanism:", scenario$mechanism))
    print(paste("Sample size:", scenario$sample_size))
    print(paste("Rho:", scenario$rho))
    print(paste("MissingRate:", scenario$missing_rate))
    return(resultsDf[0, ])  # Return empty dataframe with correct structure
  }
  
  # Fill the original dataframe structure
  if (nrow(all_results) > 0) {
    # Update simulation numbers to be sequential
    all_results$sim <- rep(1:(nrow(all_results)/3), each = 3)
    
    # Fill the pre-allocated dataframe
    n_successful <- nrow(all_results)
    resultsDf[1:n_successful, ] <- all_results
    
    # Return only the filled portion
    #return(resultsDf[1:n_successful, ])
    return(list(
        dfResults = resultsDf[1:n_successful, ],
        violations = all_violations
    ))
  } else {
    warning("No successful simulations completed")
    return(resultsDf[0, ])  # Return empty dataframe with correct structure
    return(list(
        dfResults = resultsDf[0, ],
        violations = all_violations
    ))
  }
}



extract_metrics <- function(simsum_obj, name, add_prefix = FALSE) {
  summary_obj <- summary(simsum_obj)

  # Extract key metrics with parameter identification
  metrics <- data.frame(
    method = name,
    parameter = c("A0", "A1", "A2"),
    bias = summary_obj$summ[summary_obj$summ$stat == "bias", "est"],
    bias_mcse = summary_obj$summ[summary_obj$summ$stat == "bias", "mcse"],
    empirical_se = summary_obj$summ[summary_obj$summ$stat == "empse", "est"],
    empirical_se_mcse = summary_obj$summ[summary_obj$summ$stat == "empse", "mcse"],
    model_se = summary_obj$summ[summary_obj$summ$stat == "modelse", "est"],
    coverage = summary_obj$summ[summary_obj$summ$stat == "cover", "est"],
    coverage_mcse = summary_obj$summ[summary_obj$summ$stat == "cover", "mcse"],
    power = summary_obj$summ[summary_obj$summ$stat == "power", "est"],
    power_mcse = summary_obj$summ[summary_obj$summ$stat == "power", "mcse"],
    mse = summary_obj$summ[summary_obj$summ$stat == "mse", "est"],
    rel_error_se = summary_obj$summ[summary_obj$summ$stat == "relprec", "est"]
  )
  
  # Apply prefix to all column names except 'method' if requested
  prefix <- ifelse(add_prefix, "uw_", "")
  
  metrics_wide <- metrics %>%
    tidyr::pivot_wider(
      names_from = parameter,
      values_from = c(bias, bias_mcse, empirical_se, empirical_se_mcse, model_se,
                      coverage, coverage_mcse, power, power_mcse, mse, rel_error_se),
      names_glue = paste0("{parameter}_", prefix, "{.value}")
    )

  return(metrics_wide)
}



# Load demographics table
demographics <- read.csv(file.path(eavePath, "data/multimorbidity.csv"), stringsAsFactors = TRUE)
demographics$SCSIMD5 <- as.factor(demographics$SCSIMD5)
demographics$NumComorbidities <- as.factor(demographics$NumComorbidities)
demographics <- demographics[!is.na(demographics$SCSIMD5), ]

levels(demographics$AgeGroup) <- gsub("\\+", "more", gsub("-", "to", levels(demographics$AgeGroup)))

K <- 2 # Number of visits minus one

# Parameters for allocation of treatment to individuals
gammas <- list()
gammas[[1]] <- c(
  -1.5,
  -0.05,
  rep(0.1, nlevels(demographics$AgeGroup)-1),
  rep(-0.05, nlevels(demographics$SCSIMD5)-1),
  rep(0.1, nlevels(demographics$NumComorbidities)-1)
)
gammas[[2]] <- c(
  -1.5,
  -0.05,
  rep(0.1, nlevels(demographics$AgeGroup)-1),
  rep(-0.05, nlevels(demographics$SCSIMD5)-1),
  rep(0.1, nlevels(demographics$NumComorbidities)-1),
  -0.5
)
gammas[[3]] <- c(
  -1.5,
  -0.05,
  rep(0.1, nlevels(demographics$AgeGroup)-1),
  rep(-0.05, nlevels(demographics$SCSIMD5)-1),
  rep(0.1, nlevels(demographics$NumComorbidities)-1),
  0, -0.5
)

# Parameters for confounding mechanism
thetas <- c(
  1,
  rep(2, nlevels(demographics$AgeGroup)-1),
  rep(1, nlevels(demographics$SCSIMD5)-1),
  rep(2, nlevels(demographics$NumComorbidities)-1)
)

# Possible values of tretment allocation vector
a_k_values <- c(
#  "", 
  "0", "1", 
  "00", "01", "10", "11", 
  "000", "001", "010", "011", "100", "101", "110", "111" #,
)



# Scenario creation
scenarios = create_full_factorial_scenarios()
#scenarios = create_baseline_scenarios()

n_scenarios <- length(scenarios)  # Replace with actual number
exclusion_colnames <- c("CCA_", "SMI_", "HD_", "MI_", "full_", "summary")
exclusion_summaries <- matrix(NA, nrow = n_scenarios, ncol = length(exclusion_colnames))
colnames(exclusion_summaries) <- exclusion_colnames
print(n_scenarios)
extreme_coefficient_cutoff = 100

# violations
violation_colnames <- c("CCA_", "SMI_", "HD_", "MI_", "full_", "summary")
violation_summaries <- matrix(NA, nrow = n_scenarios, ncol = length(violation_colnames))
colnames(violation_summaries) <- violation_colnames

# extreme ses
seExtreme_colnames <- c("CCA_", "SMI_", "HD_", "MI_", "full_", "summary")
seExtreme_summaries <- matrix(NA, nrow = n_scenarios, ncol = length(seExtreme_colnames))
colnames(seExtreme_summaries) <- seExtreme_colnames

source(file.path(eavePath, "script/aux_functions.R"))
source(file.path(eavePath, "script/simulate_data.R"))

total_start_time <- Sys.time()

for (s in 1:length(scenarios)) {
  start_time <- Sys.time()
  scenario <- scenarios[[s]]

  rho <- rep(scenario$rho, K+1)

  # set effect size per scenario spec
  betas <- list()
  betas[[1]] <- c(-3.5, 0.825)
  betas[[2]] <- c(-3.5, 0.825, 0.825)
  betas[[3]] <- c(-3.5, 0, 0.825, 0.825)

  exclusion_summaries[s, paste0("summary")] <- paste("Mechanism:", scenario$mechanism, 
                                            "| Sample size:", scenario$sample_size, 
                                            "| Rho:", scenario$rho, 
                                            "| MissingRate:", scenario$missing_rate)
  violation_summaries[s, paste0("summary")] <- paste("Mechanism:", scenario$mechanism, 
                                            "| Sample size:", scenario$sample_size, 
                                            "| Rho:", scenario$rho, 
                                            "| MissingRate:", scenario$missing_rate)

  source(file.path(eavePath, "script/estimate_cdf.R"))
  
  # first run full-data model
  n_sims <- 500
  n_params <- 3
  total_rows <- n_sims * n_params

  print(paste("Scenario", s, "of", length(scenarios), "| Mechanism:", scenario$mechanism, "| Sample size:", scenario$sample_size, "| Rho:", scenario$rho, "| MissingRate:", scenario$missing_rate))

  dfResults <- data.frame(
    sim = integer(total_rows),
    method = character(total_rows),
    parameter = character(total_rows),
    true_value = numeric(total_rows),
    estimate = numeric(total_rows),
    se = numeric(total_rows),
    unweighted_estimate = numeric(total_rows),
    unweighted_se = numeric(total_rows)
  )
  res = estimate_performance_parallel(dfResults, n_sims, scenario$sample_size, "None")

  dfResults <- res$dfResults
  violations <- res$violations

  # Filter out extreme estimates before simsum
  exclusion_rate <- round(100 * sum(abs(dfResults$estimate) > extreme_coefficient_cutoff) / nrow(dfResults), 1)
  exclusion_summaries[s, "full_"] <- exclusion_rate
  violation_summaries[s, "full_"] <- round(mean(unlist(violations), na.rm = TRUE), 3)
  seExtreme_summaries[s, "full_"] <- round(mean(dfResults$se[dfResults$se > 1000], na.rm = TRUE), 3)
  dfResults <- dfResults %>%
     filter(abs(estimate) <= extreme_coefficient_cutoff)

  avg_bias <- mean(dfResults$estimate - dfResults$true_value, na.rm = TRUE)
  print(paste("Average bias:", avg_bias))
  print(paste("Average se:", mean(dfResults$se, na.rm = TRUE)))

  dfResults$lower_ci <- dfResults$estimate - 1.96 * dfResults$se
  dfResults$upper_ci <- dfResults$estimate + 1.96 * dfResults$se
  coverage <- mean(dfResults$lower_ci <= dfResults$true_value & 
                  dfResults$upper_ci >= dfResults$true_value, na.rm = TRUE)
  print(paste("Coverage:", round(coverage, 3)))

  full_results <- simsum(data = dfResults, 
                    estvarname = "estimate", 
                    true = "true_value", 
                    se = "se", 
                    methodvar = "method",
                    by = "parameter",
                    ref= "weighted")
  dfResults["estimate"] <- dfResults$unweighted_estimate
  dfResults["se"] <- dfResults$unweighted_se
  full_results_unweighted <- simsum(data = dfResults, 
                    estvarname = "estimate", 
                    true = "true_value", 
                    se = "se", 
                    methodvar = "method",
                    by = "parameter",
                    ref= "weighted")

  #print("Full metrics:")
  #metr <- extract_metrics(full_results, "full_")
  #print(as.data.frame(metr))

  #run model again with missingness and methods
  methods <- c("CCA", "SMI", "HD", "MI")
  dfMetrics <- list()
  for(method in methods)
  {
    dfResults <- data.frame(
      sim = integer(total_rows),
      method = character(total_rows),
      parameter = character(total_rows),
      true_value = numeric(total_rows),
      estimate = numeric(total_rows),
      se = numeric(total_rows),
      unweighted_estimate = numeric(total_rows),
      unweighted_se = numeric(total_rows)
    )
    print(paste("Running method:", method))
    res = estimate_performance_parallel(dfResults, n_sims, scenario$sample_size, method)

    dfResults <- res$dfResults
    violations <- res$violations

    # Filter out extreme estimates before simsum
    exclusion_rate <- round(100 * sum(abs(dfResults$estimate) > extreme_coefficient_cutoff) / nrow(dfResults), 1)
    exclusion_summaries[s, paste0(method, '_')] <- exclusion_rate
    violation_summaries[s, paste0(method, '_')] <- round(mean(unlist(violations), na.rm = TRUE), 3)  
    seExtreme_summaries[s, "full_"] <- round(mean(dfResults$se[dfResults$se > 1000], na.rm = TRUE), 3)  
    dfResults <- dfResults %>%
      filter(abs(estimate) <= extreme_coefficient_cutoff)

    avg_bias <- mean(dfResults$estimate - dfResults$true_value, na.rm = TRUE)
    print(paste("Average bias for method:", method, ": ", avg_bias))
    print(paste("Average se for method:", method, ": ", mean(dfResults$se, na.rm = TRUE)))
    dfResults$lower_ci <- dfResults$estimate - 1.96 * dfResults$se
    dfResults$upper_ci <- dfResults$estimate + 1.96 * dfResults$se
    coverage <- mean(dfResults$lower_ci <= dfResults$true_value & 
                    dfResults$upper_ci >= dfResults$true_value, na.rm = TRUE)
    print(paste("Coverage for method:", method, ":", round(coverage, 3)))

    miss_results <- simsum(data = dfResults, 
                      estvarname = "estimate", 
                      true = "true_value", 
                      se = "se", 
                      methodvar = "method",
                      by = "parameter")
    
    dfResults["estimate"] <- dfResults$unweighted_estimate
    dfResults["se"] <- dfResults$unweighted_se
    miss_results_unweighted <- simsum(data = dfResults, 
                      estvarname = "estimate", 
                      true = "true_value", 
                      se = "se", 
                      methodvar = "method",
                      by = "parameter")

    # Extract metrics for missingness methods
    miss_metrics <- extract_metrics(miss_results, paste(method, "_", sep = ""))
    miss_metrics_unweighted <- extract_metrics(miss_results_unweighted, paste(method, "_unweighted_", sep = ""), add_prefix = TRUE)
    miss_metrics_all <- dplyr::bind_cols(miss_metrics, miss_metrics_unweighted[, -which(names(miss_metrics_unweighted) == "method")])
    dfMetrics <- dplyr::bind_rows(dfMetrics, miss_metrics_all)  




########################## DEBUG ##########################
  combined_results <- do.call(rbind, dfResults)
  #combined_results <- as.data.frame(combined_results)

  combined_results_fixed <- as.data.frame(t(combined_results))
  colnames(combined_results_fixed) <- c("sim", "method", "parameter", "true_value", "estimate", "se")

  # Convert to proper types
  combined_results_fixed$estimate <- as.numeric(combined_results_fixed$estimate)
  combined_results_fixed$true_value <- as.numeric(combined_results_fixed$true_value)

  # Summary by parameter
  # for(param in unique(combined_results_fixed$parameter)) {
  #   param_data <- combined_results_fixed[combined_results_fixed$parameter == param, ]
    
  #   cat("\n=== Parameter:", param, "===\n")
  #   cat("True value:", unique(param_data$true_value), "\n")
  #   cat("Mean estimate:", mean(param_data$estimate, na.rm = TRUE), "\n")
  #   cat("Median estimate:", median(param_data$estimate, na.rm = TRUE), "\n")
  #   cat("SD:", sd(param_data$estimate, na.rm = TRUE), "\n")
  #   cat("Bias (mean - true):", mean(param_data$estimate, na.rm = TRUE) - unique(param_data$true_value), "\n")
  #   cat("Count:", nrow(param_data), "\n")
  # }

  # extreme_values = c()
  # cat(paste("Missing rate:", scenario$missing_rate, "| Mechanism:", scenario$mechanism, "| Rho:", scenario$rho, "| Sample size:", scenario$sample_size, "| Effect size:", scenario$effect_size, "\n"))
  # for(param in c("A0", "A1", "A2")) {
  #   param_data <- combined_results_fixed[combined_results_fixed$parameter == param, ]
  #   true_val <- unique(param_data$true_value)
    
  #   # Find extreme estimates
  #   extreme_mask <- abs(param_data$estimate - true_val) > 2
  #   extreme_count <- sum(extreme_mask)
  #   extreme_values <- param_data$estimate[extreme_mask]
    
  #   cat("\n=== Parameter", param, "===\n")
  #   cat("True value:", true_val, "\n")
  #   cat("Extreme estimates:", extreme_count, "out of", nrow(param_data), "\n")
    
  #   if(extreme_count > 0) {
  #     cat("Extreme values:\n")
  #     print(sort(extreme_values))
  #   }
  # }

  # if (length(extreme_values) > 0) {
  #   #print("results with extreme values:")
  #   #print(head(combined_results_fixed, 100))  # Print first 10 rows of dfResults
  # }

##### DEBUGGING END #####








  }

  print(paste("violation rate: ", violation_summaries[s, ]))
  print(paste("exclusion rate: ", exclusion_summaries[s, ]))
  print(paste("extreme SEs: ", seExtreme_summaries[s, ]))

  # Extract metrics from full and append to results
  full_metrics <- extract_metrics(full_results, "full_")
  full_metrics_unweighted <- extract_metrics(full_results_unweighted, "full_unweighted_", add_prefix = TRUE)
  full_metrics_all <- dplyr::bind_cols(full_metrics, full_metrics_unweighted[, -which(names(full_metrics_unweighted) == "method")])
  dfMetrics <- dplyr::bind_rows(dfMetrics, full_metrics_all)

  scenario$metrics <- dfMetrics
  scenarios[[s]] <- scenario

  end_time <- Sys.time()
  elapsed_time <- difftime(end_time, start_time, units = "secs")
  print(paste("Scenario", s, "completed in", round(elapsed_time, 2), "seconds"))

  total_elapsed_time_so_far <- difftime(end_time, total_start_time, units = "secs")
  print(paste("total start time:", total_start_time))
  print(paste("Scenarios so far:", s))
  print(paste("Time for all scenarios so far:", round(total_elapsed_time_so_far, 2), "seconds"))
  print("========================================")
}

print("Exclusion Summary:")
print(exclusion_summaries)

exclusion = as.data.frame(t(exclusion_summaries))
csv_path <- file.path(pythonPath, "exclusion_summary.csv")
write.csv(exclusion, csv_path, row.names = FALSE)

violations = as.data.frame(t(violation_summaries))
csv_path <- file.path(pythonPath, "violation_summary.csv")
write.csv(violations, csv_path, row.names = FALSE)

seExtremes = as.data.frame(t(seExtreme_summaries))
csv_path <- file.path(pythonPath, "seExtreme_summary.csv")
write.csv(seExtremes, csv_path, row.names = FALSE)

print_scenarios_to_csv(scenarios = scenarios)
print("ALL SCENARIOS COMPLETED\n")

total_end_time <- Sys.time()
total_elapsed_time <- difftime(total_end_time, total_start_time, units = "secs")
print(paste("Total scenarios:", length(scenarios)))
print(paste("Total time for all scenarios:", round(total_elapsed_time, 2), "seconds"))