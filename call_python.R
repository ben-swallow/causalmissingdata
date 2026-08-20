library(reticulate)
library(tidyverse)


call_python <- function(df, scenario, missingnessMethod) {  
  python_script_path = file.path(pythonPath, "pipeline_python.py")
  py_run_file(python_script_path)
  
  target_vars_vector <- unlist(scenario$target_vars)
  predictors_vector <- unlist(scenario$predictors)

  # convert df to python
  py$r_df <- df

  py$scenario_mechanism <- scenario$mechanism
  py$scenario_target_vars <- as.list(target_vars_vector)
  py$scenario_predictors <- as.list(predictors_vector)
  py$scenario_missing_rate <- scenario$missing_rate
  py$scenario_method <- missingnessMethod

  py_run_string("result_df = pipeline_python(
    r_df, 
    scenario_mechanism,
    scenario_target_vars, 
    scenario_predictors,
    scenario_missing_rate, 
    scenario_method
)
")
  
  # convert result back to R
  result <- py$result_df

  return(result)
}