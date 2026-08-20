
simulate_single_dataset <- function(sample_size) {
  # Initialise matrices to store variables
  N <- sample_size
  K <- 2
  a <- matrix(NA, nrow = N, ncol = K+1); colnames(a) <- paste0("A", 0:K)
  y <- cbind(
    matrix(1,  nrow = N, ncol = 1),
    matrix(NA, nrow = N, ncol = K+1)
  ); colnames(y) <- paste0("Y", 0:(K+1))

  # Step 1. Sample B ~ p(B). Set k = 0
  b <- demographics[sample(1:nrow(demographics), size = N, replace = TRUE, prob = demographics$n), -ncol(demographics)]
  # Variables age, SCSIMD5 and NumComorbidities are coded as ordinal predictors
  b_coded <- cbind(
    encode_binary(b$Sex, name = "Sex"),
    encode_ordinal(b$AgeGroup, name = "AgeGroup"),
    encode_ordinal(b$SCSIMD5, name = "SCSIMD5"),
    encode_ordinal(b$NumComorbidities, name = "NumComorbidities")
  )

  # In the first iteration, all subjects are alive (Y0 = 1 for every subject)
  failed <- rep(FALSE, N)
  survived <- rep(TRUE, N)
  failures <- rep(K+1, N)
  Nsurvived <- N

  # For every visit k=0,...,K, we iterate Steps 2-8 of the algorithm
  for (k in 0:K) {
    # (Skip) Step 2. Sample time-varying covariates
    
    # Step 3. Sample A_k ~ p(A_k | B, \bar{A}_{k-1}, Y_k = 1)
    if (k == 0) {
      linpred.a <- as.vector(cbind(rep(1, Nsurvived), b_coded[which(survived), ]) %*% gammas[[k+1]])
    } else {
      linpred.a <- as.vector(cbind(rep(1, Nsurvived), b_coded[which(survived), ], a[which(survived), 1:k]) %*% gammas[[k+1]])
    }
    a[survived, k+1] <- as.integer(runif(Nsurvived) < expit(linpred.a))
    a[!survived, k+1] <- NA
  
    # Step 4. Calculate H_k
    h <- as.vector(b_coded[survived, ] %*% thetas)
  
    # Step 5. Calculate U_H, Z_H. Use risk score as in Appendix H
    if (k == 0) {
      a_bar <- as.character(a[,1]) # This is the history of allocated treatments, to date
    } else {
      a_bar <- apply(a[survived,1:(k+1)], 1, function(x) paste(x, collapse = ""))
    }
    
    # Initialize vectors for CDF bounds
    u_h <- rep(0, Nsurvived)
    u_h_min <- rep(0, Nsurvived)
    u_h_max <- rep(0, Nsurvived)
    
    # Fixed approach for handling discrete CDF values
    for (aa in unique(a_bar)) {
      mask <- (a_bar == aa)
      h_vals <- h[mask]
      
      # Get the empirical CDF function for this treatment allocation
      F_aa <- fhat[[aa]]
      
      # For each unique h value, find its left and right CDF values
      unique_h_vals <- unique(h_vals)
      for (h_val in unique_h_vals) {
        indices <- which(mask & h == h_val)
        
        # Right limit (standard CDF value)
        u_max <- F_aa(h_val)
        
        # Left limit (CDF just before this value)
        # Use a small epsilon to get the left limit
        u_min <- F_aa(h_val - .Machine$double.eps)
        
        u_h_min[indices] <- u_min
        u_h_max[indices] <- u_max
      }
    }
    
    u_h <- runif(Nsurvived, u_h_min, u_h_max)
    z_h <- qnorm(u_h)
  
    # Step 6. Sample Z_Y  and calculate U_Y
    z_y <- rnorm(Nsurvived, rho[k+1]*z_h, sqrt(1-rho[k+1]^2))
    u_y <- pnorm(z_y)
  
    # Step 7. Compute Y_{k+1}
    if (k == 0) {
      linpred.y <- as.vector(cbind(matrix(1, nrow = Nsurvived, ncol = 1), a[, 1]) %*% betas[[1]])
    } else {
      linpred.y <- as.vector(cbind(matrix(1, nrow = Nsurvived, ncol = 1), a[survived, 1:(k+1)]) %*% betas[[k+1]])
    }
    failed[failed == FALSE] <- u_y < expit(linpred.y)
    y[, k+2] <- ifelse(failed, 0, 1)
    survived <- !failed
    Nsurvived <- sum(survived)
  
    # Step 8. Set k = k + 1 and return to Step 2
  }

  failure_times <- rowSums(y)

  # First compute weights
  w <- matrix(1, N, K+1)
  model.fits <- list()
  for (k in 1:(K+1)) {
    if (k == 1) {
      fit.numer <- glm(a[, 1] ~ 1, family = binomial)
      fit.denom <- glm(a[, 1] ~ b_coded, family = binomial)
    } else {
      fit.numer <- glm(a[, k] ~ a[,(1:(k-1))], family = binomial, subset = which(failure_times>=k))
      fit.denom <- glm(a[, k] ~ a[,(1:(k-1))] + b_coded, family = binomial, subset = which(failure_times>=k))
    }
  
    phat.denom <- a[failure_times>=k, k] * fitted(fit.denom) + (1-a[failure_times>=k, k]) * (1- fitted(fit.denom))
    phat.numer <- a[failure_times>=k, k] * fitted(fit.numer) + (1-a[failure_times>=k, k]) * (1- fitted(fit.numer))
    if (k == 1) {
      w[, k] <- phat.numer / phat.denom
    } else {
      w[failure_times>=k, k] <- w[failure_times>=k,k-1] * phat.numer / phat.denom
    }
  }

  return(list(
      a = a,
      y = y, 
      b = b
    ))
}