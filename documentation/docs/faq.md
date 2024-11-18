# Frequently Asked Questions (FAQ)

#### 1. What is Predico?

   - Predico is a Collaborative Forecasting Platform designed to improve forecasting accuracy by facilitating collaboration between Market Makers (e.g., wind farm owners, grid operators) and Forecasters. It operates through API interactions only and has no front-end interface.


#### 2. Who are the main participants?

   - **Market Maker**: An entity that owns resources or manages grids, publishing forecasting challenges and funding the sessions. 
   - **Forecaster**: An individual or organization that submits forecasts to compete for prize money in response to challenges published by Market Makers.


#### 3. How do Market Sessions and Challenges work?

   - **Market Session**: A daily period during which Market Makers can publish forecasting challenges, and Forecasters can submit their forecasts.
   - **Market** Challenge: A specific forecasting opportunity provided by a Market Maker, specifying details like target variables, time resolution and forecast horizon.


#### 4. Who can I contact for more information?

   - For any inquiries, you can reach out to the developers at [predico-support@lists.inesctec.pt](mailto:predico-support@lists.inesctec.pt).

Feel free to consult the API documentation for technical details and guidelines on submission formats.


#### 5. How are forecasts submitted?

   - Forecasts must be submitted via HTTPs requests to the platform's API before the Gate Closure Time.
   - You can only submit or update one forecast per variable per session. The most recent valid submission before the Gate Closure Time is considered.


#### 6. What are the rules for submitting forecasts?

   - **Gate Closure Time**: Forecasts must be submitted on time; late submissions are not accepted.
   - **Forecast Resolution**: Forecasts must match the 15-minute time resolution requirement.
   - **Coverage**: Forecasts should cover the entire specified period providing up to 96 forecasted values per variable per day (adjusted for daylight saving time - 92/100 values in march/october DST change days, respectively).


#### 7. How are forecasts evaluated and scored?

   - In deterministic forecasting, forecasters are assessed and ranked according to their Root Mean Squared Error (RMSE). 
In contrast, forecasters are ranked based on pinball loss when evaluating forecasts at the 10th and 90th percentiles. In both cases, a lower value indicates a higher ranking for the forecaster.

   - Regarding prize distribution, it is done based on rank with 50% of the market value distributed to top-ranking Forecasters, and 50% based on the contribution to the ensemble forecast.
