**Deliverable:** Create `hw01/prompt_comparison.md` with the following for each strategy:
1. The complete prompt you sent (copy it exactly)
2. The first 150 words of Claude's response
3. Your evaluation: what did this strategy do well? What was missing or generic?  

**Strategy #1: Zero-Shot**  
1. The complete prompt you sent (copy it exactly)  
What are the most important metrics for measuring credit risk in a consumer loan portfolio?  

2. The first 150 words of Claude's response   
"The core metrics for consumer loan portfolio credit risk fall into a few buckets, and the best analyses combine several rather than relying on just one.

At the account level, the starting point is usually the borrower's risk profile at origination: credit score (FICO or similar), debt-to-income ratio, loan-to-value ratio for secured loans, and payment-to-income ratio. These feed into probability of default (PD), which is often modeled by credit score band or through logistic regression on borrower characteristics. Loss given default (LGD) captures what the lender actually loses once a default happens, net of any recovery or collateral value, and exposure at default (EAD) captures how much is outstanding at that point. Multiplying PD × LGD × EAD gives expected loss, which is the standard building block for reserving (this is essentially the CECL framework banks now use).

At the portfolio level, the most commonly tracked figures are delinquency rates"  

3. Your evaluation: what did this strategy do well? What was missing or generic?     
I thought this response was fairly good. It was not super specific and felt a little overly technical, but it did a decent job of explaining common default reasons.

**Strategy #2: Role-assigned**
1. The complete prompt you sent (copy it exactly)  
You are a financial advisor to first time borrowers. One of them asks "What are the most important metrics for measuring credit risk in a consumer loan portfolio?"  

2. The first 150 words of Claude's response  
"Credit risk in a consumer loan portfolio is usually tracked through a handful of complementary metrics, since no single number tells the whole story. The most fundamental is delinquency rate — the share of loans that are late on payments, typically broken into buckets like 30, 60, and 90+ days past due. Lenders watch how loans migrate between these buckets ("roll rates") because a loan that rolls from 30 to 60 days late is much more likely to eventually default than one that stays put. Closely related is the default or charge-off rate, which measures the percentage of loans a lender ultimately writes off as uncollectible, often expressed as an annualized rate against total outstanding balances. Probability of default (PD) is the forward-looking version of this: a statistical estimate of how likely a borrower is to default over a given time horizon, usually derived from credit scores, payment history, and"  

3. Your evaluation: what did this strategy do well? What was missing or generic?    
I liked how this response spoke in more basic terms. I could tell Claude understood that first time borrowers would relate better to simpler language compared to Strategy #1. I also liked how Claude disclosed at the end that is was not a financial advisor to protect from liability. One thing I wished Claude did was make the response shorter. A first time borrower might be overwhelmed by how long the response was. 

**Strategy #3: Few Shot** 
1. The complete prompt you sent (copy it exactly)  
"For the following question, please provide 3-6 brief bullet points that best answer the question. For example, if I asked what the top reasons for going to college, your response might be

- To get a degree and improve future career outlook
- To learn about subjects you find interesting
- To experience living away from home for the first time
- To meet new people through groups on campus  

Here is the question I want you to answer: What are the most important metrics for measuring credit risk in a consumer loan portfolio?"  

2. The first 150 words of Claude's response  
- "Delinquency and default rates – the share of borrowers falling behind (30/60/90+ days past due) or defaulting outright, typically tracked by vintage and cohort to see how each origination period is performing over time.
- Credit scores (FICO/VantageScore) and score migration – both the distribution of scores at origination and how borrowers' scores drift afterward, which signals portfolio quality and early warning of deterioration.
- Debt-to-income (DTI) and loan-to-value (LTV) ratios – underwriting metrics that capture a borrower's capacity to repay and the collateral cushion on secured loans.
- Probability of default, loss given default, and exposure at default (PD/LGD/EAD) – the core inputs used to calculate expected credit losses under frameworks like CECL/IFRS 9."  

3. Your evaluation: what did this strategy do well? What was missing or generic?  
I think Claude did a good job of keeping the bulleted responses brief like I requested. I could tell Claude wanted to explain in more detail because it gave me exactly 6 bullet points after I told it to make between 3 and 6. While this response is generic and simple, that was exactly what I prompted Claude to create.

**Conclusion section (required): Write 3–5 sentences comparing the three strategies. Which produced the most useful output for a BI analyst, and why?**    
While all three strategies have their strengths, I think the third strategy has the most value to a BI analyst. As a BI analysts, these professionals need to balance technical skills with business knowledge. The brief bullet points in Strategy #3 would allow an analyst to quickly consume an overview of the business process without being caught up in too many details. However, if the BI analyst sought to gain a more in depth knowledge of this process, Strategy #1 might be better because it is much more detailed. 

---
