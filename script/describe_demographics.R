library(arsenal)

#setwd("C:/Users/the_o/Desktop/Dissertation/SynthesisationRepo/eave_ii_simulated_data")

N <- 1e3
rhos <- c(-0.1, -0.3, -0.5, -0.7, -0.9)

b <- rbind(
  read.csv(paste0("simulations/", 1, "/confounders.csv"), header = TRUE),
  read.csv(paste0("simulations/", 2, "/confounders.csv"), header = TRUE),
  read.csv(paste0("simulations/", 3, "/confounders.csv"), header = TRUE),
  read.csv(paste0("simulations/", 4, "/confounders.csv"), header = TRUE),
  read.csv(paste0("simulations/", 5, "/confounders.csv"), header = TRUE)
)
b$rho <- rep(rhos, each = N)
b <- b[, c(5, 1, 3, 4, 2)]
b$SCSIMD5 <- as.factor(b$SCSIMD5)
b$NumComorbidities <- as.factor(b$NumComorbidities)
levels(b$Sex) <- c("Female", "Male")
levels(b$AgeGroup) <- gsub("years", "", levels(b$AgeGroup))
levels(b$SCSIMD5) <- c("1 (Most deprived)", 2:4, "5 (Least deprived)")
levels(b$NumComorbidities) <- c(0:3, "4+")
tabledem <- tableby(rho ~ Sex + SCSIMD5 + NumComorbidities + AgeGroup, data = b, total = FALSE, test = FALSE)
labels(tabledem) <- c(
  Overall   = "Total", 
  Sex   = "Sex", 
  AgeGroup   = "Age Group", 
  SCSIMD5   = "SCSIMD5", 
  NumComorbidities   = "Number of comorbidities")
print(summary(tabledem, text = "latex"))

