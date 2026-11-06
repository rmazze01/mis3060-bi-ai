# Model metadata

Exported from the `hw06.pbix` model in Power BI DAX query view, using `INFO.VIEW.TABLES()`, `INFO.VIEW.COLUMNS()` and `INFO.VIEW.RELATIONSHIPS()`. Tab-separated, unedited. Measures were not exported.

## Tables

```text
[ID]	[Name]	[Model]	[DataCategory]	[Description]	[IsHidden]	[StorageMode]	[TableStorage]	[Expression]	[ShowAsVariationOnly]	[IsPrivate]	[CalculationGroupPrecedence]	[LineageTag]
12	fact_transactions	0e9e8b9b-17b8-45ad-a328-ff1df54cdbb2	Regular		false	Import	fact transactions (12)		false	false		a4ac2403-156b-4240-91cf-3a06a58e0569
15	DateTableTemplate_b50879b8-a09d-4fd7-b9a6-7a34995295aa	0e9e8b9b-17b8-45ad-a328-ff1df54cdbb2	Regular		true	Import	DateTableTemplate b50879b8 a09d 4fd7 b9a6 7a34995295aa (15)	Calendar(Date(2015,1,1), Date(2015,1,1))	false	true		c8639ee7-91c4-41ff-868a-33a2ed4c13db
888	fact_portfolio_snapshot	0e9e8b9b-17b8-45ad-a328-ff1df54cdbb2	Regular		false	Import	fact portfolio snapshot (888)		false	false		21d61f92-199f-40bd-b6c4-95a2fb307ff4
1660	fact_fees	0e9e8b9b-17b8-45ad-a328-ff1df54cdbb2	Regular		false	Import	fact fees (1660)		false	false		80af5c69-00b1-48f2-95d1-5a0f6fb2a5c5
2230	dim_advisor	0e9e8b9b-17b8-45ad-a328-ff1df54cdbb2	Regular		false	Import	dim advisor (2230)		false	false		d181ad82-fcea-46aa-9e35-bdfaa98f32ab
2501	dim_benchmark	0e9e8b9b-17b8-45ad-a328-ff1df54cdbb2	Regular		false	Import	dim benchmark (2501)		false	false		3d760a83-cac5-4bde-8859-a636472f24c9
2656	dim_client	0e9e8b9b-17b8-45ad-a328-ff1df54cdbb2	Regular		false	Import	dim client (2656)		false	false		f60500f1-f0a9-4e92-88fe-5cb6c4735bba
2659	LocalDateTable_976ce71a-eea0-49bb-b089-dd421adaa4b8	0e9e8b9b-17b8-45ad-a328-ff1df54cdbb2	Regular		true	Import	LocalDateTable 976ce71a eea0 49bb b089 dd421adaa4b8 (2659)	Calendar(Date(Year(MIN('dim_client'[client_since])), 1, 1), Date(Year(MAX('dim_client'[client_since])), 12, 31))	true	false		17822824-2438-4b56-be02-d1912b602671
3492	dim_date	0e9e8b9b-17b8-45ad-a328-ff1df54cdbb2	Regular		false	Import	dim date (3492)		false	false		f29230fd-5a2e-4a63-9e17-0ae7d57386ff
3495	LocalDateTable_30b0d5f8-768e-4d2a-9562-888fa2f9b2e7	0e9e8b9b-17b8-45ad-a328-ff1df54cdbb2	Regular		true	Import	LocalDateTable 30b0d5f8 768e 4d2a 9562 888fa2f9b2e7 (3495)	Calendar(Date(Year(MIN('dim_date'[date])), 1, 1), Date(Year(MAX('dim_date'[date])), 12, 31))	true	false		a73bb761-9324-4b2b-9fd9-d9bf3066ab2d
4194	dim_security	0e9e8b9b-17b8-45ad-a328-ff1df54cdbb2	Regular		false	Import	dim security (4194)		false	false		e7fbf2fc-bc20-445d-b8e4-925fac11625f
4729	_Measures	0e9e8b9b-17b8-45ad-a328-ff1df54cdbb2	Regular		false	Import	Table (4729)	ROW ("Placeholder", BLANK ())
	false	false		10fa56e0-de6b-403b-9f48-1ca4775fe62d
```

## Columns

```text
[ID]	[Name]	[Table]	[DataType]	[DataCategory]	[Description]	[IsHidden]	[IsUnique]	[IsKey]	[IsNullable]	[Alignment]	[SummarizeBy]	[ColumnStorage]	[Type]	[SourceColumn]	[Expression]	[FormatString]	[IsAvailableInMDX]	[SortByColumn]	[GroupingBehavior]	[SourceProviderType]	[DisplayFolder]	[AlternateOf]	[LineageTag]
13	RowNumber-2662979B-1795-4F74-8F37-6A1BA8059B61	fact_transactions	Integer	RowNumber		true	true	true	false	Default	Default	fact transactions (12)$RowNumber 2662979B 1795 4F74 8F37 6A1BA8059B61 (13)	RowNumber	RowNumber-2662979B-1795-4F74-8F37-6A1BA8059B61			true		GroupOnValue				
22	txn_id	fact_transactions	Integer	Regular		false	false	false	true	Default	Sum	fact transactions (12)$txn id (22)	Data	txn_id		0	true		GroupOnValue				2f7ea2b4-6768-4161-a8c0-1ff06d03f9cb
23	client_id	fact_transactions	Integer	Regular		false	false	false	true	Default	None	fact transactions (12)$client id (23)	Data	client_id		0	true		GroupOnValue				4b863a86-6bbf-41a4-b1f6-533e858c694e
24	advisor_id	fact_transactions	Integer	Regular		false	false	false	true	Default	None	fact transactions (12)$advisor id (24)	Data	advisor_id		0	true		GroupOnValue				16fc4d7b-9222-4b11-b068-228200520665
25	security_id	fact_transactions	Integer	Regular		false	false	false	true	Default	None	fact transactions (12)$security id (25)	Data	security_id		0	true		GroupOnValue				85f28aff-5c5f-4a6a-a4fa-0e6794b6b9ce
26	txn_date	fact_transactions	Date	Regular		false	false	false	true	Default	None	fact transactions (12)$txn date (26)	Data	txn_date		Long Date	true		GroupOnValue				b47a7170-a39f-4971-a86e-3037defbec11
41	txn_type	fact_transactions	Text	Regular		false	false	false	true	Default	None	fact transactions (12)$txn type (41)	Data	txn_type			true		GroupOnValue				264bc7f5-1755-4496-bf11-3f3b8ef7376e
42	shares	fact_transactions	Number	Regular		false	false	false	true	Default	Sum	fact transactions (12)$shares (42)	Data	shares			true		GroupOnValue				13e85051-1046-4c2f-ac23-af28ec218155
43	price	fact_transactions	Number	Regular		false	false	false	true	Default	Sum	fact transactions (12)$price (43)	Data	price			true		GroupOnValue				4e273108-5ee6-4c7e-a30a-1e56d1f48c4d
44	amount	fact_transactions	Number	Regular		false	false	false	true	Default	Sum	fact transactions (12)$amount (44)	Data	amount			true		GroupOnValue				3011ecc8-8591-4325-9a8f-fa8b7d5f94da
45	is_post_departure_txn	fact_transactions	Integer	Regular		false	false	false	true	Default	Sum	fact transactions (12)$is post departure txn (45)	Data	is_post_departure_txn		0	true		GroupOnValue				5fbb37d0-b864-4197-b6c4-f0e000d6a831
16	RowNumber-2662979B-1795-4F74-8F37-6A1BA8059B61	DateTableTemplate_b50879b8-a09d-4fd7-b9a6-7a34995295aa	Integer	RowNumber		true	true	true	false	Default	Default	DateTableTemplate b50879b8 a09d 4fd7 b9a6 7a34995295aa (15)$RowNumber 2662979B 1795 4F74 8F37 6A1BA8059B61 (16)	RowNumber	RowNumber-2662979B-1795-4F74-8F37-6A1BA8059B61			true		GroupOnValue				
27	Date	DateTableTemplate_b50879b8-a09d-4fd7-b9a6-7a34995295aa	Date	PaddedDateTableDates		true	false	false	true	Default	None	DateTableTemplate b50879b8 a09d 4fd7 b9a6 7a34995295aa (15)$Date (27)	CalculatedTableColumn	Date		General Date	true		GroupOnValue				648b75a3-541b-45be-8fbf-d3f82fd37ae8
28	Year	DateTableTemplate_b50879b8-a09d-4fd7-b9a6-7a34995295aa	Integer	Years		true	false	false	true	Default	None	DateTableTemplate b50879b8 a09d 4fd7 b9a6 7a34995295aa (15)$Year (28)	Calculated		YEAR([Date])	0	true		GroupOnValue				263db08e-f8f3-4acb-862f-4589e2a16b56
29	MonthNo	DateTableTemplate_b50879b8-a09d-4fd7-b9a6-7a34995295aa	Integer	MonthOfYear		true	false	false	true	Default	None	DateTableTemplate b50879b8 a09d 4fd7 b9a6 7a34995295aa (15)$MonthNo (29)	Calculated		MONTH([Date])	0	true		GroupOnValue				7cef0390-d5e9-44ed-b3da-bcf46470a4ee
30	Month	DateTableTemplate_b50879b8-a09d-4fd7-b9a6-7a34995295aa	Text	Months		true	false	false	true	Default	None	DateTableTemplate b50879b8 a09d 4fd7 b9a6 7a34995295aa (15)$Month (30)	Calculated		FORMAT([Date], "MMMM")		true	MonthNo	GroupOnValue				af8b6781-5614-4beb-a575-ceb5a4d098de
31	QuarterNo	DateTableTemplate_b50879b8-a09d-4fd7-b9a6-7a34995295aa	Integer	QuarterOfYear		true	false	false	true	Default	None	DateTableTemplate b50879b8 a09d 4fd7 b9a6 7a34995295aa (15)$QuarterNo (31)	Calculated		INT(([MonthNo] + 2) / 3)	0	true		GroupOnValue				2088e750-7815-4a85-907f-6d72c5fbe8ba
32	Quarter	DateTableTemplate_b50879b8-a09d-4fd7-b9a6-7a34995295aa	Text	Quarters		true	false	false	true	Default	None	DateTableTemplate b50879b8 a09d 4fd7 b9a6 7a34995295aa (15)$Quarter (32)	Calculated		"Qtr " & [QuarterNo]		true	QuarterNo	GroupOnValue				f3609a6d-1283-425e-ae11-fcaac095d30c
33	Day	DateTableTemplate_b50879b8-a09d-4fd7-b9a6-7a34995295aa	Integer	DayOfMonth		true	false	false	true	Default	None	DateTableTemplate b50879b8 a09d 4fd7 b9a6 7a34995295aa (15)$Day (33)	Calculated		DAY([Date])	0	true		GroupOnValue				5ac573d0-79d2-4581-a114-66210662108a
889	RowNumber-2662979B-1795-4F74-8F37-6A1BA8059B61	fact_portfolio_snapshot	Integer	RowNumber		true	true	true	false	Default	Default	fact portfolio snapshot (888)$RowNumber 2662979B 1795 4F74 8F37 6A1BA8059B61 (889)	RowNumber	RowNumber-2662979B-1795-4F74-8F37-6A1BA8059B61			true		GroupOnValue				
895	snapshot_id	fact_portfolio_snapshot	Integer	Regular		false	false	false	true	Default	Sum	fact portfolio snapshot (888)$snapshot id (895)	Data	snapshot_id		0	true		GroupOnValue				f94517bf-5c0a-49d4-825a-d793e26dbc79
896	client_id	fact_portfolio_snapshot	Integer	Regular		false	false	false	true	Default	None	fact portfolio snapshot (888)$client id (896)	Data	client_id		0	true		GroupOnValue				c6819015-a8b6-4313-9f13-1bd7d5d980ac
897	advisor_id	fact_portfolio_snapshot	Integer	Regular		false	false	false	true	Default	None	fact portfolio snapshot (888)$advisor id (897)	Data	advisor_id		0	true		GroupOnValue				5c8a58e2-8c8f-44b5-959e-05461d5fb82c
898	benchmark_id	fact_portfolio_snapshot	Integer	Regular		false	false	false	true	Default	None	fact portfolio snapshot (888)$benchmark id (898)	Data	benchmark_id		0	true		GroupOnValue				8c2a598b-f866-4881-8736-0375bfa16d1c
899	snapshot_date	fact_portfolio_snapshot	Date	Regular		false	false	false	true	Default	None	fact portfolio snapshot (888)$snapshot date (899)	Data	snapshot_date		Long Date	true		GroupOnValue				d8b52da9-2ccc-4c07-bf72-829cafbaec4e
907	Year	fact_portfolio_snapshot	Integer	Regular		false	false	false	true	Default	Sum	fact portfolio snapshot (888)$year (907)	Data	year		0	true		GroupOnValue				3df99dd0-b72d-48e6-9435-e307590fdfbf
908	Month	fact_portfolio_snapshot	Integer	Regular		false	false	false	true	Default	Sum	fact portfolio snapshot (888)$month (908)	Data	month		0	true		GroupOnValue				ab0b26c7-c5de-49a6-a4a0-ef22400fa2a8
909	aum	fact_portfolio_snapshot	Number	Regular		false	false	false	true	Default	Sum	fact portfolio snapshot (888)$aum (909)	Data	aum			true		GroupOnValue				be8a635b-1197-400f-827b-fbac1e756a02
910	return_ytd	fact_portfolio_snapshot	Number	Regular		false	false	false	true	Default	Sum	fact portfolio snapshot (888)$return ytd (910)	Data	return_ytd			true		GroupOnValue				b7ae1105-4ff4-476e-b713-4a741ac66bce
911	benchmark_return_ytd	fact_portfolio_snapshot	Number	Regular		false	false	false	true	Default	Sum	fact portfolio snapshot (888)$benchmark return ytd (911)	Data	benchmark_return_ytd			true		GroupOnValue				2b8fb6ae-86e6-43b7-bab0-ef1b342b9b97
912	active_alpha_ytd	fact_portfolio_snapshot	Number	Regular		false	false	false	true	Default	Sum	fact portfolio snapshot (888)$active alpha ytd (912)	Data	active_alpha_ytd			true		GroupOnValue				4570bf12-2262-4aa6-bad0-c2930db8ae8b
913	cash_pct	fact_portfolio_snapshot	Number	Regular		false	false	false	true	Default	Sum	fact portfolio snapshot (888)$cash pct (913)	Data	cash_pct			true		GroupOnValue				21f37617-1e7c-4e6a-b52f-1e479c9ce7ab
914	account_type	fact_portfolio_snapshot	Text	Regular		false	false	false	true	Default	None	fact portfolio snapshot (888)$account type (914)	Data	account_type			true		GroupOnValue				db2f6a63-b394-47d0-a0de-53430821f703
915	is_return_suspect	fact_portfolio_snapshot	Integer	Regular		false	false	false	true	Default	Sum	fact portfolio snapshot (888)$is return suspect (915)	Data	is_return_suspect		0	true		GroupOnValue				41a97754-15fe-4baa-ba1f-b05ea9a77da8
1661	RowNumber-2662979B-1795-4F74-8F37-6A1BA8059B61	fact_fees	Integer	RowNumber		true	true	true	false	Default	Default	fact fees (1660)$RowNumber 2662979B 1795 4F74 8F37 6A1BA8059B61 (1661)	RowNumber	RowNumber-2662979B-1795-4F74-8F37-6A1BA8059B61			true		GroupOnValue				
1667	fee_id	fact_fees	Integer	Regular		false	false	false	true	Default	Sum	fact fees (1660)$fee id (1667)	Data	fee_id		0	true		GroupOnValue				fb640d91-8e4e-49f8-8b35-c599d9cebe1e
1668	client_id	fact_fees	Integer	Regular		false	false	false	true	Default	None	fact fees (1660)$client id (1668)	Data	client_id		0	true		GroupOnValue				3855071b-7cec-4fc5-a0e8-299a517262a1
1669	advisor_id	fact_fees	Integer	Regular		false	false	false	true	Default	None	fact fees (1660)$advisor id (1669)	Data	advisor_id		0	true		GroupOnValue				53e7be3d-bc61-46a3-a9c3-7eac263133a3
1670	fee_date	fact_fees	Date	Regular		false	false	false	true	Default	None	fact fees (1660)$fee date (1670)	Data	fee_date		Long Date	true		GroupOnValue				8cf53540-eb60-4105-80ef-5a91ce0419a9
1678	fee_type	fact_fees	Text	Regular		false	false	false	true	Default	None	fact fees (1660)$fee type (1678)	Data	fee_type			true		GroupOnValue				41273d04-ca62-4fc3-8385-2f3c2465d52d
1679	aum_basis	fact_fees	Number	Regular		false	false	false	true	Default	Sum	fact fees (1660)$aum basis (1679)	Data	aum_basis			true		GroupOnValue				7e414100-ad20-4847-8304-3af0d33e6624
1680	bps_charged	fact_fees	Number	Regular		false	false	false	true	Default	Sum	fact fees (1660)$bps charged (1680)	Data	bps_charged			true		GroupOnValue				3cd35b34-b3c7-4f4f-b283-16dcac2d3166
1681	amount	fact_fees	Number	Regular		false	false	false	true	Default	Sum	fact fees (1660)$amount (1681)	Data	amount			true		GroupOnValue				ac2c74b2-22b8-4471-b5da-aca50082e6ed
2231	RowNumber-2662979B-1795-4F74-8F37-6A1BA8059B61	dim_advisor	Integer	RowNumber		true	true	true	false	Default	Default	dim advisor (2230)$RowNumber 2662979B 1795 4F74 8F37 6A1BA8059B61 (2231)	RowNumber	RowNumber-2662979B-1795-4F74-8F37-6A1BA8059B61			true		GroupOnValue				
2233	advisor_id	dim_advisor	Integer	Regular		false	true	false	false	Default	None	dim advisor (2230)$advisor id (2233)	Data	advisor_id		0	true		GroupOnValue				a2e7cc64-73fb-4caf-853d-31e02acc893f
2234	first_name	dim_advisor	Text	Regular		false	false	false	true	Default	None	dim advisor (2230)$first name (2234)	Data	first_name			true		GroupOnValue				e7bce820-670d-42fd-b889-353ab3d53ca5
2235	last_name	dim_advisor	Text	Regular		false	false	false	true	Default	None	dim advisor (2230)$last name (2235)	Data	last_name			true		GroupOnValue				a213abdf-2067-4972-a34e-4330fec6e4c9
2236	region	dim_advisor	Text	Regular		false	false	false	true	Default	None	dim advisor (2230)$region (2236)	Data	region			true		GroupOnValue				c3dd2d12-9ddb-4e9c-b4c9-dcf3bc9403a3
2237	years_experience	dim_advisor	Integer	Regular		false	false	false	true	Default	Sum	dim advisor (2230)$years experience (2237)	Data	years_experience		0	true		GroupOnValue				d837a55d-350e-4a99-8f55-eed121eca9bf
2238	aum_target_mm	dim_advisor	Integer	Regular		false	false	false	true	Default	Sum	dim advisor (2230)$aum target mm (2238)	Data	aum_target_mm		0	true		GroupOnValue				6aecd1a0-99fb-474e-a2a5-abce3156f5ba
2239	certifications	dim_advisor	Text	Regular		false	false	false	true	Default	None	dim advisor (2230)$certifications (2239)	Data	certifications			true		GroupOnValue				ac925ce7-6f36-4271-a749-abfc8459110d
2502	RowNumber-2662979B-1795-4F74-8F37-6A1BA8059B61	dim_benchmark	Integer	RowNumber		true	true	true	false	Default	Default	dim benchmark (2501)$RowNumber 2662979B 1795 4F74 8F37 6A1BA8059B61 (2502)	RowNumber	RowNumber-2662979B-1795-4F74-8F37-6A1BA8059B61			true		GroupOnValue				
2504	benchmark_id	dim_benchmark	Integer	Regular		false	true	false	false	Default	None	dim benchmark (2501)$benchmark id (2504)	Data	benchmark_id		0	true		GroupOnValue				eaf81098-729d-436f-83ec-51ba5e7267cd
2505	name	dim_benchmark	Text	Regular		false	false	false	true	Default	None	dim benchmark (2501)$name (2505)	Data	name			true		GroupOnValue				dcfdcc48-d748-4117-85a0-f57e2bf3d12d
2506	asset_class	dim_benchmark	Text	Regular		false	false	false	true	Default	None	dim benchmark (2501)$asset class (2506)	Data	asset_class			true		GroupOnValue				e9586a46-e329-402b-978c-8242fd113d09
2507	ticker_proxy	dim_benchmark	Text	Regular		false	false	false	true	Default	None	dim benchmark (2501)$ticker proxy (2507)	Data	ticker_proxy			true		GroupOnValue				dd9c54f2-a258-4493-b4f8-286f1bb88a7a
2657	RowNumber-2662979B-1795-4F74-8F37-6A1BA8059B61	dim_client	Integer	RowNumber		true	true	true	false	Default	Default	dim client (2656)$RowNumber 2662979B 1795 4F74 8F37 6A1BA8059B61 (2657)	RowNumber	RowNumber-2662979B-1795-4F74-8F37-6A1BA8059B61			true		GroupOnValue				
2663	client_id	dim_client	Integer	Regular		false	true	false	false	Default	None	dim client (2656)$client id (2663)	Data	client_id		0	true		GroupOnValue				073be2c8-1c28-4040-9618-17fc490ab4dd
2664	first_name	dim_client	Text	Regular		false	false	false	true	Default	None	dim client (2656)$first name (2664)	Data	first_name			true		GroupOnValue				855c5ee7-195b-4ee2-9e51-46d9a18a674a
2665	last_name	dim_client	Text	Regular		false	false	false	true	Default	None	dim client (2656)$last name (2665)	Data	last_name			true		GroupOnValue				ef358d26-1fcc-45fc-ab0a-3092b7f504d5
2666	age	dim_client	Integer	Regular		false	false	false	true	Default	Sum	dim client (2656)$age (2666)	Data	age		0	true		GroupOnValue				b432940e-bc51-41dd-834e-bc0f31013025
2667	city	dim_client	Text	Regular		false	false	false	true	Default	None	dim client (2656)$city (2667)	Data	city			true		GroupOnValue				fadb2514-f780-46b4-af31-7733c6dc6bb8
2668	state	dim_client	Text	Regular		false	false	false	true	Default	None	dim client (2656)$state (2668)	Data	state			true		GroupOnValue				2bbb2c5d-b32c-4f3e-823e-e605f882c574
2669	zip_code	dim_client	Text	Regular		false	false	false	true	Default	None	dim client (2656)$zip code (2669)	Data	zip_code			true		GroupOnValue				0bbb57d6-a705-44a2-a2dd-3e4f3dc62ed6
2670	risk_profile	dim_client	Text	Regular		false	false	false	true	Default	None	dim client (2656)$risk profile (2670)	Data	risk_profile			true		GroupOnValue				bc4ed04d-f6e6-4e4c-aabc-4032c9466d23
2671	client_tier	dim_client	Text	Regular		false	false	false	true	Default	None	dim client (2656)$client tier (2671)	Data	client_tier			true		GroupOnValue				da1a863e-a888-4225-abb9-29fa2257e4fa
2672	primary_account_type	dim_client	Text	Regular		false	false	false	true	Default	None	dim client (2656)$primary account type (2672)	Data	primary_account_type			true		GroupOnValue				0457c728-a9b1-4ffd-86de-da463c2d7792
2673	initial_aum	dim_client	Number	Regular		false	false	false	true	Default	Sum	dim client (2656)$initial aum (2673)	Data	initial_aum			true		GroupOnValue				c7a9daf4-d97e-408b-9846-a8eabc7019e8
2674	client_since	dim_client	Date	Regular		false	false	false	true	Default	None	dim client (2656)$client since (2674)	Data	client_since		Long Date	true		GroupOnValue				6f312f55-f626-49e5-8cac-5ce4794ec9bd
2682	advisor_id	dim_client	Integer	Regular		false	false	false	true	Default	Sum	dim client (2656)$advisor id (2682)	Data	advisor_id		0	true		GroupOnValue				e53b47b9-172f-43af-9db9-eb8c364e92cd
2683	is_active	dim_client	True/False	Regular		false	false	false	true	Default	None	dim client (2656)$is active (2683)	Data	is_active		"TRUE";"TRUE";"FALSE"	true		GroupOnValue				1af65b9e-402d-482c-99ce-959e41d1e0aa
2660	RowNumber-2662979B-1795-4F74-8F37-6A1BA8059B61	LocalDateTable_976ce71a-eea0-49bb-b089-dd421adaa4b8	Integer	RowNumber		true	true	true	false	Default	Default	LocalDateTable 976ce71a eea0 49bb b089 dd421adaa4b8 (2659)$RowNumber 2662979B 1795 4F74 8F37 6A1BA8059B61 (2660)	RowNumber	RowNumber-2662979B-1795-4F74-8F37-6A1BA8059B61			true		GroupOnValue				
2675	Date	LocalDateTable_976ce71a-eea0-49bb-b089-dd421adaa4b8	Date	PaddedDateTableDates		true	true	false	false	Default	None	LocalDateTable 976ce71a eea0 49bb b089 dd421adaa4b8 (2659)$Date (2675)	CalculatedTableColumn	Date		General Date	true		GroupOnValue				eb78a13f-9dd2-419a-b91e-6be18e67c234
2676	Year	LocalDateTable_976ce71a-eea0-49bb-b089-dd421adaa4b8	Integer	Years		true	false	false	true	Default	None	LocalDateTable 976ce71a eea0 49bb b089 dd421adaa4b8 (2659)$Year (2676)	Calculated		YEAR([Date])	0	true		GroupOnValue				d9b3a0ac-3668-4a31-9731-fac1a02a318f
2677	MonthNo	LocalDateTable_976ce71a-eea0-49bb-b089-dd421adaa4b8	Integer	MonthOfYear		true	false	false	true	Default	None	LocalDateTable 976ce71a eea0 49bb b089 dd421adaa4b8 (2659)$MonthNo (2677)	Calculated		MONTH([Date])	0	true		GroupOnValue				ef733f13-3532-46a1-bc79-8a149c2c17ad
2678	Month	LocalDateTable_976ce71a-eea0-49bb-b089-dd421adaa4b8	Text	Months		true	false	false	true	Default	None	LocalDateTable 976ce71a eea0 49bb b089 dd421adaa4b8 (2659)$Month (2678)	Calculated		FORMAT([Date], "MMMM")		true	MonthNo	GroupOnValue				95c024f7-0a57-4779-ac05-074fced07313
2679	QuarterNo	LocalDateTable_976ce71a-eea0-49bb-b089-dd421adaa4b8	Integer	QuarterOfYear		true	false	false	true	Default	None	LocalDateTable 976ce71a eea0 49bb b089 dd421adaa4b8 (2659)$QuarterNo (2679)	Calculated		INT(([MonthNo] + 2) / 3)	0	true		GroupOnValue				40c1b9e7-b5d7-4566-b1c6-6b960dc4608d
2680	Quarter	LocalDateTable_976ce71a-eea0-49bb-b089-dd421adaa4b8	Text	Quarters		true	false	false	true	Default	None	LocalDateTable 976ce71a eea0 49bb b089 dd421adaa4b8 (2659)$Quarter (2680)	Calculated		"Qtr " & [QuarterNo]		true	QuarterNo	GroupOnValue				4bd1aa18-3b20-445e-a2ad-e0b88493f58e
2681	Day	LocalDateTable_976ce71a-eea0-49bb-b089-dd421adaa4b8	Integer	DayOfMonth		true	false	false	true	Default	None	LocalDateTable 976ce71a eea0 49bb b089 dd421adaa4b8 (2659)$Day (2681)	Calculated		DAY([Date])	0	true		GroupOnValue				36a68bc6-960d-44b7-aedd-dc27214d9431
3493	RowNumber-2662979B-1795-4F74-8F37-6A1BA8059B61	dim_date	Integer	RowNumber		true	true	true	false	Default	Default	dim date (3492)$RowNumber 2662979B 1795 4F74 8F37 6A1BA8059B61 (3493)	RowNumber	RowNumber-2662979B-1795-4F74-8F37-6A1BA8059B61			true		GroupOnValue				
3499	date_id	dim_date	Integer	Regular		false	false	false	true	Default	Sum	dim date (3492)$date id (3499)	Data	date_id		0	true		GroupOnValue				9b319164-7794-4326-ba5a-9464d57128d0
3500	Date	dim_date	Date	Regular		false	true	false	false	Default	None	dim date (3492)$date (3500)	Data	Date		Long Date	true		GroupOnValue				7334aa01-acf8-44b0-a93c-0c817fc066cf
3508	Year	dim_date	Integer	Regular		false	false	false	true	Default	Sum	dim date (3492)$year (3508)	Data	year		0	true		GroupOnValue				235c816f-53be-4ebf-9b91-c2e44a80c31d
3509	Quarter	dim_date	Integer	Regular		false	false	false	true	Default	Sum	dim date (3492)$quarter (3509)	Data	quarter		0	true		GroupOnValue				9ba4c887-fd03-4f6a-b1d2-bb44b348a293
3510	Month	dim_date	Integer	Regular		false	false	false	true	Default	Sum	dim date (3492)$month (3510)	Data	month		0	true		GroupOnValue				12597f7b-b2ce-4ff8-b4e8-ba8ef6a7a6bd
3511	month_name	dim_date	Text	Regular		false	false	false	true	Default	None	dim date (3492)$month name (3511)	Data	month_name			true		GroupOnValue				997f8095-48e1-45aa-a561-09f1b3a776d8
3512	week_of_year	dim_date	Integer	Regular		false	false	false	true	Default	Sum	dim date (3492)$week of year (3512)	Data	week_of_year		0	true		GroupOnValue				4a7eedeb-bbf6-4c5f-98bd-00adbe46df20
3513	day_of_week	dim_date	Text	Regular		false	false	false	true	Default	None	dim date (3492)$day of week (3513)	Data	day_of_week			true		GroupOnValue				fd243baf-b07d-4112-bc25-e4b2f95f479f
3514	is_month_end	dim_date	Integer	Regular		false	false	false	true	Default	Sum	dim date (3492)$is month end (3514)	Data	is_month_end		0	true		GroupOnValue				b5ef44bb-f63e-428d-9e2f-e79a3457befa
3515	is_quarter_end	dim_date	Integer	Regular		false	false	false	true	Default	Sum	dim date (3492)$is quarter end (3515)	Data	is_quarter_end		0	true		GroupOnValue				2eae20a1-9da4-40fa-8089-4f2e363d9204
3516	is_year_end	dim_date	Integer	Regular		false	false	false	true	Default	Sum	dim date (3492)$is year end (3516)	Data	is_year_end		0	true		GroupOnValue				2cf682a5-888c-447f-b322-1f4ce47f6db4
3517	is_trading_day	dim_date	Integer	Regular		false	false	false	true	Default	Sum	dim date (3492)$is trading day (3517)	Data	is_trading_day		0	true		GroupOnValue				f537cfde-849d-4cbd-94ed-6a9dc683caf6
3496	RowNumber-2662979B-1795-4F74-8F37-6A1BA8059B61	LocalDateTable_30b0d5f8-768e-4d2a-9562-888fa2f9b2e7	Integer	RowNumber		true	true	true	false	Default	Default	LocalDateTable 30b0d5f8 768e 4d2a 9562 888fa2f9b2e7 (3495)$RowNumber 2662979B 1795 4F74 8F37 6A1BA8059B61 (3496)	RowNumber	RowNumber-2662979B-1795-4F74-8F37-6A1BA8059B61			true		GroupOnValue				
3501	Date	LocalDateTable_30b0d5f8-768e-4d2a-9562-888fa2f9b2e7	Date	PaddedDateTableDates		true	true	false	false	Default	None	LocalDateTable 30b0d5f8 768e 4d2a 9562 888fa2f9b2e7 (3495)$Date (3501)	CalculatedTableColumn	Date		General Date	true		GroupOnValue				4c03b502-5dad-40ab-97cd-23557ca732a4
3502	Year	LocalDateTable_30b0d5f8-768e-4d2a-9562-888fa2f9b2e7	Integer	Years		true	false	false	true	Default	None	LocalDateTable 30b0d5f8 768e 4d2a 9562 888fa2f9b2e7 (3495)$Year (3502)	Calculated		YEAR([Date])	0	true		GroupOnValue				5acf7074-e4fd-47d1-8551-c9f22744778a
3503	MonthNo	LocalDateTable_30b0d5f8-768e-4d2a-9562-888fa2f9b2e7	Integer	MonthOfYear		true	false	false	true	Default	None	LocalDateTable 30b0d5f8 768e 4d2a 9562 888fa2f9b2e7 (3495)$MonthNo (3503)	Calculated		MONTH([Date])	0	true		GroupOnValue				07651b01-ab3e-4cc8-ba8e-8fa48bb474d9
3504	Month	LocalDateTable_30b0d5f8-768e-4d2a-9562-888fa2f9b2e7	Text	Months		true	false	false	true	Default	None	LocalDateTable 30b0d5f8 768e 4d2a 9562 888fa2f9b2e7 (3495)$Month (3504)	Calculated		FORMAT([Date], "MMMM")		true	MonthNo	GroupOnValue				aacc90bb-0cb4-4625-bb7d-98b5515cd70d
3505	QuarterNo	LocalDateTable_30b0d5f8-768e-4d2a-9562-888fa2f9b2e7	Integer	QuarterOfYear		true	false	false	true	Default	None	LocalDateTable 30b0d5f8 768e 4d2a 9562 888fa2f9b2e7 (3495)$QuarterNo (3505)	Calculated		INT(([MonthNo] + 2) / 3)	0	true		GroupOnValue				bdcd12b0-95fe-4b3d-80dc-ba03e7134e2b
3506	Quarter	LocalDateTable_30b0d5f8-768e-4d2a-9562-888fa2f9b2e7	Text	Quarters		true	false	false	true	Default	None	LocalDateTable 30b0d5f8 768e 4d2a 9562 888fa2f9b2e7 (3495)$Quarter (3506)	Calculated		"Qtr " & [QuarterNo]		true	QuarterNo	GroupOnValue				a8e1ad16-6b46-406f-a315-e0d9a3d4b14e
3507	Day	LocalDateTable_30b0d5f8-768e-4d2a-9562-888fa2f9b2e7	Integer	DayOfMonth		true	false	false	true	Default	None	LocalDateTable 30b0d5f8 768e 4d2a 9562 888fa2f9b2e7 (3495)$Day (3507)	Calculated		DAY([Date])	0	true		GroupOnValue				85f76d82-b976-4360-8d17-c4ad47c92ab6
4195	RowNumber-2662979B-1795-4F74-8F37-6A1BA8059B61	dim_security	Integer	RowNumber		true	true	true	false	Default	Default	dim security (4194)$RowNumber 2662979B 1795 4F74 8F37 6A1BA8059B61 (4195)	RowNumber	RowNumber-2662979B-1795-4F74-8F37-6A1BA8059B61			true		GroupOnValue				
4197	security_id	dim_security	Integer	Regular		false	true	false	false	Default	None	dim security (4194)$security id (4197)	Data	security_id		0	true		GroupOnValue				acd54eb0-d93f-4267-99cd-ab4e6ae7afe7
4198	ticker	dim_security	Text	Regular		false	false	false	true	Default	None	dim security (4194)$ticker (4198)	Data	ticker			true		GroupOnValue				a5ce0614-c1a5-4476-8abf-f7635f8f7419
4199	name	dim_security	Text	Regular		false	false	false	true	Default	None	dim security (4194)$name (4199)	Data	name			true		GroupOnValue				49b91db0-a5d8-4fef-98d8-fff0d72060fc
4200	asset_class	dim_security	Text	Regular		false	false	false	true	Default	None	dim security (4194)$asset class (4200)	Data	asset_class			true		GroupOnValue				e9d41c2a-a6b2-490a-9bc3-b61c04505e47
4201	sector	dim_security	Text	Regular		false	false	false	true	Default	None	dim security (4194)$sector (4201)	Data	sector			true		GroupOnValue				a7fc978f-18d5-418d-804c-26b28a01a1f3
4202	benchmark_id	dim_security	Integer	Regular		false	false	false	true	Default	None	dim security (4194)$benchmark id (4202)	Data	benchmark_id		0	true		GroupOnValue				a7f9a5f8-0905-48f6-b5b2-f77f1299c2de
4203	is_etf	dim_security	True/False	Regular		false	false	false	true	Default	None	dim security (4194)$is etf (4203)	Data	is_etf		"TRUE";"TRUE";"FALSE"	true		GroupOnValue				291b7aa3-e866-4965-ba0a-8e84d5d7f5c1
4204	expense_ratio_bps	dim_security	Integer	Regular		false	false	false	true	Default	Sum	dim security (4194)$expense ratio bps (4204)	Data	expense_ratio_bps		0	true		GroupOnValue				34623055-7f57-4e3f-96c7-d0ba80c42139
4730	RowNumber-2662979B-1795-4F74-8F37-6A1BA8059B61	_Measures	Integer	RowNumber		true	true	true	false	Default	Default	Table (4729)$RowNumber 2662979B 1795 4F74 8F37 6A1BA8059B61 (4730)	RowNumber	RowNumber-2662979B-1795-4F74-8F37-6A1BA8059B61			true		GroupOnValue				
4779	Placeholder	_Measures	Integer	Regular		true	false	false	true	Default	Sum	Table (4729)$Placeholder (4779)	CalculatedTableColumn	Placeholder		0	true		GroupOnValue				d6e7e7c6-003c-433e-a920-0f1a3046ed37
```

## Relationships

```text
[ID]	[Name]	[Relationship]	[Model]	[IsActive]	[CrossFilteringBehavior]	[RelyOnReferentialIntegrity]	[FromTable]	[FromColumn]	[FromCardinality]	[ToTable]	[ToColumn]	[ToCardinality]	[State]	[SecurityFilteringBehavior]
2450	AutoDetected_47d2c78f-3915-4351-b30d-fc5f654a65f4	'fact_transactions'[advisor_id] *[<-]1 'dim_advisor'[advisor_id]	0e9e8b9b-17b8-45ad-a328-ff1df54cdbb2	true	OneDirection	false	fact_transactions	advisor_id	Many	dim_advisor	advisor_id	One	Ready	Single
3424	AutoDetected_080dc0c9-a847-4102-8fe6-5527ad4e80b2	'fact_transactions'[client_id] *[<-]1 'dim_client'[client_id]	0e9e8b9b-17b8-45ad-a328-ff1df54cdbb2	true	OneDirection	false	fact_transactions	client_id	Many	dim_client	client_id	One	Ready	Single
4453	AutoDetected_2f815d05-ddf4-42b9-bf11-303f56a168d6	'fact_transactions'[security_id] *[<-]1 'dim_security'[security_id]	0e9e8b9b-17b8-45ad-a328-ff1df54cdbb2	true	OneDirection	false	fact_transactions	security_id	Many	dim_security	security_id	One	Ready	Single
4712	6deec966-5197-f019-8717-87cd3326e62d	'fact_transactions'[txn_date] *[<-]1 'dim_date'[date]	0e9e8b9b-17b8-45ad-a328-ff1df54cdbb2	true	OneDirection	false	fact_transactions	txn_date	Many	dim_date	date	One	Ready	Single
2451	AutoDetected_515f758c-a4c4-4e3e-8414-fe1239270ac5	'fact_portfolio_snapshot'[advisor_id] *[<-]1 'dim_advisor'[advisor_id]	0e9e8b9b-17b8-45ad-a328-ff1df54cdbb2	true	OneDirection	false	fact_portfolio_snapshot	advisor_id	Many	dim_advisor	advisor_id	One	Ready	Single
2639	AutoDetected_27290db9-48a2-4230-a18e-ac5fca16ab64	'fact_portfolio_snapshot'[benchmark_id] *[<-]1 'dim_benchmark'[benchmark_id]	0e9e8b9b-17b8-45ad-a328-ff1df54cdbb2	true	OneDirection	false	fact_portfolio_snapshot	benchmark_id	Many	dim_benchmark	benchmark_id	One	Ready	Single
3425	AutoDetected_8da07bbb-379a-44b4-8620-2cb9df480b79	'fact_portfolio_snapshot'[client_id] *[<-]1 'dim_client'[client_id]	0e9e8b9b-17b8-45ad-a328-ff1df54cdbb2	true	OneDirection	false	fact_portfolio_snapshot	client_id	Many	dim_client	client_id	One	Ready	Single
4695	aa81e5e4-13d7-2473-c80b-1050d4fb268e	'fact_portfolio_snapshot'[snapshot_date] *[<-]1 'dim_date'[date]	0e9e8b9b-17b8-45ad-a328-ff1df54cdbb2	true	OneDirection	false	fact_portfolio_snapshot	snapshot_date	Many	dim_date	date	One	Ready	Single
2452	AutoDetected_13cb45f8-9f1d-42c6-9326-a4402ef86ceb	'fact_fees'[advisor_id] *[<-]1 'dim_advisor'[advisor_id]	0e9e8b9b-17b8-45ad-a328-ff1df54cdbb2	true	OneDirection	false	fact_fees	advisor_id	Many	dim_advisor	advisor_id	One	Ready	Single
3426	AutoDetected_6b7ee019-ebcc-4ab0-a5f6-23016186f549	'fact_fees'[client_id] *[<-]1 'dim_client'[client_id]	0e9e8b9b-17b8-45ad-a328-ff1df54cdbb2	true	OneDirection	false	fact_fees	client_id	Many	dim_client	client_id	One	Ready	Single
4678	fbd94a81-c893-0c31-c79a-9a0f84f664a0	'fact_fees'[fee_date] *[<-]1 'dim_date'[date]	0e9e8b9b-17b8-45ad-a328-ff1df54cdbb2	true	OneDirection	false	fact_fees	fee_date	Many	dim_date	date	One	Ready	Single
2662	371030ed-f05a-47f6-a233-06998810b983	'dim_client'[client_since] *[<-]1 'LocalDateTable_976ce71a-eea0-49bb-b089-dd421adaa4b8'[Date]	0e9e8b9b-17b8-45ad-a328-ff1df54cdbb2	true	OneDirection	false	dim_client	client_since	Many	LocalDateTable_976ce71a-eea0-49bb-b089-dd421adaa4b8	date	One	Ready	Single
3498	4ef23535-e977-479b-98bc-f80d9c25c9a5	'dim_date'[date] *[<-]1 'LocalDateTable_30b0d5f8-768e-4d2a-9562-888fa2f9b2e7'[Date]	0e9e8b9b-17b8-45ad-a328-ff1df54cdbb2	true	OneDirection	false	dim_date	date	Many	LocalDateTable_30b0d5f8-768e-4d2a-9562-888fa2f9b2e7	date	One	Ready	Single
4454	AutoDetected_031cb484-3962-4004-9c23-08d705a8563e	'dim_security'[benchmark_id] *[<-]1 'dim_benchmark'[benchmark_id]	0e9e8b9b-17b8-45ad-a328-ff1df54cdbb2	true	OneDirection	false	dim_security	benchmark_id	Many	dim_benchmark	benchmark_id	One	Ready	Single
```
