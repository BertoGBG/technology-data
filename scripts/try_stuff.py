def get_industrial_data_DEA(tech, data_in, expectation=None):
    """
    interpolate cost for a given technology from DEA database sheet

    uncertainty can be "optimist", "pessimist" or None|""
    """
    excel_file = get_sheet_location(tech, sheet_names, data_in)
    if excel_file is None:
        print("excel file not found for tech ", tech)
        return None

    if tech == "battery":
        usecols = "B:J"
    elif tech in ['direct air capture', 'cement capture', 'biomass CHP capture']:
        usecols = "A:F"
    elif tech in ['industrial heat pump medium temperature', 'industrial heat pump high temperature',
                  'electric boiler steam', "gas boiler steam", "solid biomass boiler steam",
                  "solid biomass boiler steam CC", "direct firing gas", "direct firing gas CC",
                  "direct firing solid fuels", "direct firing solid fuels CC"]:
        usecols = "A:E"
    elif tech in ['Fischer-Tropsch', 'Haber-Bosch', 'air separation unit']:
        usecols = "B:F"
    elif tech in ["central water-sourced heat pump"]:
        usecols = "B,I,K"
    else:
        usecols = "B:G"

    usecols += f",{uncrtnty_lookup[tech]}"

    if ((tech in cost_year_2019) or (tech in cost_year_2020) or ("renewable_fuels" in excel_file)):
        skiprows = [0]
    else:
        skiprows = [0, 1]

    excel = pd.read_excel(excel_file,
                          sheet_name=sheet_names[tech],
                          index_col=0,
                          usecols=usecols,
                          skiprows=skiprows,
                          na_values="N.A")
    # print(excel)

    excel.dropna(axis=1, how="all", inplace=True)

    excel.index = excel.index.fillna(" ")
    excel.index = excel.index.astype(str)
    excel.dropna(axis=0, how="all", inplace=True)
    # print(excel)