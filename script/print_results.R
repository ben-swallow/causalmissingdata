library(xtable)

#setwd("C:/Users/the_o/Desktop/Dissertation/SynthesisationRepo/eave_ii_simulated_data/")

rhos <- c(-0.1, -0.3, -0.5, -0.7, -0.9)

for(l in 1:length(rhos)) {
  #results_table <- read.csv(paste0("output/", l, "/results.csv"))
  results_table <- param.estimates
  rownames(results_table) <- paste0("$\\beta_{", c("00", "01", "10", "11", "12", "20", "21", "22", "23"), "}$")
  colnames(results_table) <- c("True value", "Unweighted Estimate", "SD", "Weighted Estimate", "SD")
  
  cat("\n=== LaTeX Table for RHO =", rhos[l], "===\n")
  print(results_table)
  #print(
  #  xtable(
   #   results_table, 
    #  caption = paste0("Parameter estimates for unweighted and weighted model fits to the dataset simulated with $\\rho_k$ = ", rhos[l]), 
     # label = paste0("table:results",l)), 
  #  type = "latex", 
   # sanitize.text.function=identity
  #)
}
