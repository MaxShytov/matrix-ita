from flask import Flask, render_template, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# pip install Flask[async]
from flask import Flask, render_template, request, jsonify
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
from flask_cors import CORS

# import asyncio

from playwright.async_api import async_playwright, expect
from datetime import datetime
import time

app = Flask(__name__)

# Разрешаем запросы с любых источников, включая локальные файлы
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/')
def index():
    return render_template('index.html')



arrCabin = {
    'Y': '2',  # Economy Class / 2 - Premium Economy
    'S': '2',  # Premium economy
    'C': '3',  # Business class / 3 - Business class or higher
    'J': '3',  # Premium Business class
    'F': '4',  # First class / 4 -  First class
    'P': '4',  # Prize First class
}
arr_date_modifier = {
    # "On this day only": 1,
    "Or day before": 2,
    "Or day after": 3,
    "Plus/minus 1 day": 4,
    "Plus/minus 2 days": 5,
}
arr_arrival_departure = {
    "Arrival": "arrive",
    # "Departure": "depart",
}


def getStopPoint(dt):
    str1 = ''
    for it in dt:
        if len(str1) > 0: str1 += ' '
        str1 += it['value']

    return str1


def getAirportr(dt):
    str1 = ''
    for it in dt:
        if len(str1) > 0: str1 += ' '
        str1 += it['value']

    return str1


def getDate(input_data):
    if ('DepartureDateText' in input_data) & (input_data['DepartureDateText'] != ''):
        date = input_data['DepartureDateText']
    else:
        date = datetime.fromtimestamp(input_data['DepartureDate'] / 1000)
        date = '' + date.strftime("%m") + '/' + date.strftime("%d") + '/' + date.strftime("%Y")

    return date


async def inputParamsCommon(page, inputData):
    # sales_city = input.sales_city ? input.sales_city: 'New York';
    # type('matrix-sales-city-field[formcontrolname="salesCity"] input', sales_city)
    # $('div.cdk-overlay-container mat-option').click();

    AllowAirportChanges = True
    if 'AllowAirportChanges' in inputData: AllowAirportChanges = inputData['AllowAirportChanges']
    AvailableFlightsOnly = True
    if 'AvailableFlightsOnly' in inputData: AvailableFlightsOnly = inputData['AvailableFlightsOnly']

    stopsIn = inputData['Stops']['value']
    stopsExtraIn = -1
    if 'ExtraStops' in inputData: stopsExtraIn = inputData['ExtraStops']['value']
    # {text: 'No limit', value: -1},
    # {text: 'Nonstop only', value: 0},
    # {text: 'Up to 1 stop', value: 1},
    # {text: 'Up to 2 stops', value: 2},

    cabinIn = inputData['Cabin']['value']
    currencyIn = None
    if inputData['Currency']:
        currencyIn = inputData['Currency']['value']

    # ====Passenger====
    Adults = inputData['Passengers']['Adults']['value']
    Youths = inputData['Passengers']['Youths']['value']
    Seniors = inputData['Passengers']['Seniors']['value']
    Children = inputData['Passengers']['Children']['value']
    InfantsLap = inputData['Passengers']['InfantsLap']['value']
    InfantsSea = inputData['Passengers']['InfantsSea']['value']

    if Adults > 1: await page.fill('input[formcontrolname="adults"]', str(Adults))
    if Youths: await page.fill('input[formcontrolname="youth"]', str(Youths))
    if Seniors: await page.fill('input[formcontrolname="seniors"]', str(Seniors))
    if Children: await page.fill('input[formcontrolname="children"]', str(Children))
    if InfantsLap: await page.fill('input[formcontrolname="infantsInLap"]', str(InfantsLap))
    if InfantsSea: await page.fill('input[formcontrolname="infantsInSeat"]', str(InfantsSea))

    SalesCityMatrix = 'New York'
    if 'SalesCityMatrix' in inputData: SalesCityMatrix = inputData['SalesCityMatrix']['value']
    await page.fill('matrix-sales-city-field[formcontrolname="salesCity"] input', SalesCityMatrix)

    # await page.wait_for_timeout(1001)
    await page.click('div.cdk-overlay-container div[role="listbox"] mat-option:nth-child(1)')

    if AllowAirportChanges == False:
        # await page.fill('input[id="mat-mdc-checkbox-1-input"]', AllowAirportChanges)
        await page.click('input[id="mat-mdc-checkbox-1-input"]')

    if AvailableFlightsOnly == False:
        # await page.fill('input[id="mat-mdc-checkbox-2-input"]', AvailableFlightsOnly)
        await page.click('input[id="mat-mdc-checkbox-2-input"]')

    if (stopsIn >= 0):
        stopsIn += 2
        await page.click('mat-select[formcontrolname="stops"]')
        await page.click('div.cdk-overlay-container div[role="listbox"] mat-option:nth-child(' + str(stopsIn) + ')')
    # if (stopsExtraIn >= 0):
    stopsExtraIn += 2
    await page.click('mat-select[formcontrolname="extraStops"]')
    await page.click('div.cdk-overlay-container div[role="listbox"] mat-option:nth-child(' + str(stopsExtraIn) + ')')

    if cabinIn:
        cabinMatrix = arrCabin[cabinIn]
        await page.click('mat-select[formcontrolname="cabin"]')
        await page.click('div.cdk-overlay-container div[role="listbox"] mat-option:nth-child(' + str(cabinMatrix) + ')')

    if currencyIn:
        await page.fill('matrix-currency-field[formcontrolname="currency"] input', currencyIn)
    else:
        await page.fill('matrix-currency-field[formcontrolname="currency"] input', 'USD')


async def inputParamsOneWay(page, inputData):
    date1 = getDate(inputData['flight'][0])
    # date1 = datetime.fromtimestamp(inputData['flight'][0]['DepartureDate'] / 1000)
    # date1 = '' + date1.strftime("%m") + '/' + date1.strftime("%d") + '/' + date1.strftime("%Y")

    specifyTheDay1 = inputData['flight'][0]['SpecifyTheDay']['text']
    arrivalDeparture1 = inputData['flight'][0]['ArrivalDeparture']['value']

    DepartingFrom = getStopPoint(inputData['flight'][0]['DepartingFrom'])
    Destination = getStopPoint(inputData['flight'][0]['Destination'])

    # stopPoint1 = getStopPoint(inputData['flight'][0]['StopPoint'])
    RoutingCodesMatrix = ''
    if 'RoutingCodesMatrix' in inputData['flight'][0]: RoutingCodesMatrix = inputData['flight'][0]['RoutingCodesMatrix']
    ExtensionCodesMatrix = ''
    if 'ExtensionCodesMatrix' in inputData['flight'][0]: ExtensionCodesMatrix = inputData['flight'][0][
        'ExtensionCodesMatrix']

    # await page.click('mat-tab-header div#mat-tab-label-0-1')  # OneWay
    await page.click('mat-tab-header div#mat-tab-group-0-label-1')  # OneWay

    # await page.wait_for_timeout(1001)
    await page.fill('matrix-location-field[formcontrolname="origin"] input', DepartingFrom)
    # await page.wait_for_timeout(1001)
    await page.fill('matrix-location-field[formcontrolname="dest"] input', Destination)
    # await page.wait_for_timeout(1001)
    await page.fill('.mat-datepicker-input', date1)

    # if (arr_date_modifier[specifyTheDay1]):
    if specifyTheDay1 in arr_date_modifier:
        specifyTheDay1 = arr_date_modifier[specifyTheDay1]
        await page.click('mat-select[formcontrolname="departureDateModifier"]')
        await page.click(
            'div.cdk-overlay-container div[role="listbox"] mat-option:nth-child(' + str(specifyTheDay1) + ')')

    if arrivalDeparture1 in arr_arrival_departure:
        arrivalDeparture1 = arr_arrival_departure[arrivalDeparture1]
        await page.click('mat-select[formcontrolname="departureDateType"]')
        await page.click('div.cdk-overlay-container mat-option[value="' + arrivalDeparture1 + '"]')

    # if len(stopPoint1) > 0:
    #     await page.click('form matrix-flight-picker button.mdc-button--outlined')
    #     await page.fill('input[formcontrolname="routing"]', stopPoint1)

    await page.click('form matrix-flight-picker button.mdc-button--outlined')
    if RoutingCodesMatrix: await page.fill('input[formcontrolname="routing"]', RoutingCodesMatrix)
    if ExtensionCodesMatrix: await page.fill('input[formcontrolname="ext"]', ExtensionCodesMatrix)

    PreferredTimes = 0xff
    if 'PreferredTimes' in inputData['flight'][0]: PreferredTimes = inputData['flight'][0]['PreferredTimes']
    if PreferredTimes != 0xff:
        await page.click('matrix-preferred-times button')
        # print('Prefferred---->')
        for j in range(6):
            if (PreferredTimes & (1<<j)) == 0:
                print('Preff---->', j + 1)
                preferred = page.locator('matrix-preferred-times mat-checkbox').nth(j)
                await preferred.click()


async def inputParamsMultiCity(page, inputData):
    # matrix-multi-city-search-tab matrix-flight-picker
    err = {'warning': ''}
    # await page.wait_for_timeout(1001)

    # await page.click('mat-tab-header div#mat-tab-label-0-2')  # MultiCity mat-mdc-tab-labels
    await page.click('mat-tab-header div#mat-tab-group-0-label-2')  # MultiCity mat-mdc-tab-labels

    count = len(inputData['flight'])
    i = 1
    while (i < count):
        # await page.wait_for_timeout(1001)
        # await page.click('mat-chip.mat-chip-selected[role="option"]')
        await page.click('button.add-flight')
        i += 1

    try:
        # next_element = page.query_selector("text=\"some element text\" >> + *")
        # Здесь >> означает дочерний комбинатор, + означает соседний комбинатор, а * означает любой элемент
        # element = page.locator('mat-chip.mat-chip-selected[role="option"] + *')
        element = page.locator('button.add-flight + *')
        await element.click()
    except Exception as e:
        err = {'warning': 'is not found Show Advanced Controls'}
        print("warning: is not found Show Advanced Controls")

    # try:
    #     element = page.get_by_text('Show Advanced Controls')
    #     await element.click()
    # except Exception as e:
    #     print("error: is not found Show Advanced Controls")

    # queueIsVisible = page.locator('span').filter(has_text='Show Advanced Controls').first()   #.filter({hasText: "QUEUED"}).first().isVisible()
    # ttt = await expect(page.locator('button span.mdc-button__label')).to_contain_text("Show Advanced Controls")
    # await expect(page.locator('button span.mdc-button__label')).to_contain_text(["Hide Advanced Controls"]).click()
    # await page.click('button span.mdc-button__label:contains("Show Advanced Controls")')

    i = -1
    for item in inputData['flight']:
        i += 1
        tt = page.locator('matrix-multi-city-search-tab matrix-flight-picker').nth(i)

        date1 = getDate(item)
        # date1 = datetime.fromtimestamp(item['DepartureDate'] / 1000)
        # date1 = '' + date1.strftime("%m") + '/' + date1.strftime("%d") + '/' + date1.strftime("%Y")

        specifyTheDay1 = item['SpecifyTheDay']['text']
        arrivalDeparture1 = item['ArrivalDeparture']['value']

        # stopPoint1 = getStopPoint(item['StopPoint'])
        RoutingCodesMatrix = ''
        if 'RoutingCodesMatrix' in item: RoutingCodesMatrix = item['RoutingCodesMatrix']
        ExtensionCodesMatrix = ''
        if 'ExtensionCodesMatrix' in item: ExtensionCodesMatrix = item['ExtensionCodesMatrix']

        # DepartingFrom = item['DepartingFrom'][0]['value']
        # Destination = item['Destination'][0]['value']
        DepartingFrom = getStopPoint(item['DepartingFrom'])
        Destination = getStopPoint(item['Destination'])

        await tt.locator('matrix-location-field[formcontrolname="origin"] input').fill(DepartingFrom)
        await tt.locator('matrix-location-field[formcontrolname="dest"] input').fill(Destination)
        await tt.locator('.mat-datepicker-input').fill(date1)

        if specifyTheDay1 in arr_date_modifier:
            specifyTheDay1 = arr_date_modifier[specifyTheDay1]
            await tt.locator('mat-select[formcontrolname="departureDateModifier"]').click()
            # await tt.locator(
            #     'div.cdk-overlay-container div[role="listbox"] mat-option:nth-child(' + str(
            #         specifyTheDay1) + ')').click()
            await page.click(
                'div.cdk-overlay-container div[role="listbox"] mat-option:nth-child(' + str(specifyTheDay1) + ')')

        if arrivalDeparture1 in arr_arrival_departure:
            arrivalDeparture1 = arr_arrival_departure[arrivalDeparture1]
            await tt.locator('mat-select[formcontrolname="departureDateType"]').click()
            # await tt.locator('div.cdk-overlay-container mat-option[value="' + arrivalDeparture1 + '"]').click()
            await page.click('div.cdk-overlay-container mat-option[value="' + arrivalDeparture1 + '"]')

        # if len(stopPoint1) > 0:
        #     try:
        #         await tt.locator('input[formcontrolname="routing"]').fill(stopPoint1)
        #     except Exception as e:
        #         err = {'warning': 'is not found stopPoint'}
        #         print("warning: is not found stopPoint")

        try:
            # await page.fill('input[formcontrolname="routing"]', RoutingCodesMatrix)
            # await page.fill('input[formcontrolname="ext"]', ExtensionCodesMatrix)
            if RoutingCodesMatrix: await tt.locator('input[formcontrolname="routing"]').fill(RoutingCodesMatrix)
            if ExtensionCodesMatrix: await tt.locator('input[formcontrolname="ext"]').fill(ExtensionCodesMatrix)
        except Exception as e:
            err = {'warning': 'is not found stopPoint'}
            print("warning: is not found stopPoint")

        PreferredTimes = 0xff
        if 'PreferredTimes' in item: PreferredTimes = item['PreferredTimes']
        if PreferredTimes != 0xff:
            btn = tt.locator('matrix-preferred-times button')
            await btn.click()
            # print('Prefferred---->')
            for j in range(6):
                if (PreferredTimes & (1<<j)) == 0:
                    print('PreferredTimes---->', j + 1)
                    preferred = tt.locator('matrix-preferred-times mat-checkbox').nth(j)
                    await preferred.click()

    # await page.wait_for_timeout(1001)

    return err


async def inputParamsRoundTripOld(page, inputData):
    date1 = getDate(inputData['flight'][0])

    if 'ReturnDateText' in inputData:
        date2 = inputData['ReturnDateText']
    else:
        date2 = datetime.fromtimestamp(inputData['ReturnDate'] / 1000)
        date2 = '' + date2.strftime("%m") + '/' + date2.strftime("%d") + '/' + date2.strftime("%Y")

    specifyTheDay1 = inputData['flight'][0]['SpecifyTheDay']['text']
    specifyTheDay2 = inputData['ReturnSpecifyTheDay']['text']

    arrivalDeparture1 = inputData['flight'][0]['ArrivalDeparture']['value']
    arrivalDeparture2 = inputData['ReturnArrivalDeparture']['value']

    # stopPoint1 = getStopPoint(inputData['flight'][0]['StopPoint'])
    # stopPoint2 = getStopPoint(inputData['ReturnStopPoint'])
    RoutingCodesMatrix = ''
    if 'RoutingCodesMatrix' in inputData['flight'][0]: RoutingCodesMatrix = inputData['flight'][0]['RoutingCodesMatrix']
    ExtensionCodesMatrix = ''
    if 'ExtensionCodesMatrix' in inputData['flight'][0]: ExtensionCodesMatrix = inputData['flight'][0][
        'ExtensionCodesMatrix']

    ReturnRoutingCodesMatrix = ''
    if 'ReturnRoutingCodesMatrix' in inputData: ReturnRoutingCodesMatrix = inputData['ReturnRoutingCodesMatrix']
    ReturnExtensionCodesMatrix = ''
    if 'ReturnExtensionCodesMatrix' in inputData: ReturnExtensionCodesMatrix = inputData['ReturnExtensionCodesMatrix']

    DepartingFrom = getStopPoint(inputData['flight'][0]['DepartingFrom'])
    Destination = getStopPoint(inputData['flight'][0]['Destination'])

    # await page.click('mat-tab-header div#mat-tab-label-0-0')  # RoundTrip
    await page.click('mat-tab-header div#mat-tab-group-0-label-0')  # RoundTrip

    # await page.wait_for_timeout(1001)
    await page.fill('matrix-location-field[formcontrolname="origin"] input', DepartingFrom)
    # await page.wait_for_timeout(1001)
    await page.fill('matrix-location-field[formcontrolname="dest"] input', Destination)

    # await page.wait_for_timeout(1001)
    await page.fill('mat-date-range-input .mat-start-date', date1)
    # await page.fill('mat-date-range-input .mat-start-date', '10/29/2023')
    await page.fill('mat-date-range-input .mat-end-date', date2)
    # await page.fill('mat-date-range-input .mat-end-date', '11/29/2023')
    # await page.wait_for_timeout(1001)

    if specifyTheDay1 in arr_date_modifier:
        specifyTheDay1 = arr_date_modifier[specifyTheDay1]
        await page.click('mat-select[formcontrolname="departureDateModifier"]')
        await page.click(
            'div.cdk-overlay-container div[role="listbox"] mat-option:nth-child(' + str(specifyTheDay1) + ')')
    if specifyTheDay2 in arr_date_modifier:
        specifyTheDay2 = arr_date_modifier[specifyTheDay2]
        await page.click('mat-select[formcontrolname="returnDateModifier"]')
        await page.click(
            'div.cdk-overlay-container div[role="listbox"] mat-option:nth-child(' + str(specifyTheDay2) + ')')

    if arrivalDeparture1 in arr_arrival_departure:
        arrivalDeparture1 = arr_arrival_departure[arrivalDeparture1]
        await page.click('mat-select[formcontrolname="departureDateType"]')
        await page.click('div.cdk-overlay-container mat-option[value="' + arrivalDeparture1 + '"]')
    if arrivalDeparture2 in arr_arrival_departure:
        arrivalDeparture2 = arr_arrival_departure[arrivalDeparture2]
        await page.click('mat-select[formcontrolname="returnDateType"]')
        await page.click('div.cdk-overlay-container mat-option[value="' + arrivalDeparture2 + '"]')

    # click = 0
    # if len(stopPoint1) > 0:
    #     click = 1
    #     await page.click('form matrix-flight-picker button.mdc-button--outlined')
    #     await page.fill('input[formcontrolname="routing"]', stopPoint1)
    # if len(stopPoint2) > 0:
    #     if click == 0:  await page.click('form matrix-flight-picker button.mdc-button--outlined')
    #     await page.fill('input[formcontrolname="routingRet"]', stopPoint2)

    await page.click('form matrix-flight-picker button.mdc-button--outlined')

    if RoutingCodesMatrix: await page.fill('input[formcontrolname="routing"]', RoutingCodesMatrix)
    if ExtensionCodesMatrix: await page.fill('input[formcontrolname="ext"]', ExtensionCodesMatrix)

    if ReturnRoutingCodesMatrix: await page.fill('input[formcontrolname="routingRet"]', ReturnRoutingCodesMatrix)
    if ReturnExtensionCodesMatrix: await page.fill('input[formcontrolname="extRet"]', ReturnExtensionCodesMatrix)


async def inputParamsRoundTrip(page, inputData):
    date1 = getDate(inputData['flight'][0])
    date2 = getDate(inputData['Return'])

    specifyTheDay1 = inputData['flight'][0]['SpecifyTheDay']['text']
    specifyTheDay2 = inputData['Return']['SpecifyTheDay']['text']

    arrivalDeparture1 = inputData['flight'][0]['ArrivalDeparture']['value']
    arrivalDeparture2 = inputData['Return']['ArrivalDeparture']['value']

    # stopPoint1 = getStopPoint(inputData['flight'][0]['StopPoint'])
    # stopPoint2 = getStopPoint(inputData['Return']['StopPoint'])
    RoutingCodesMatrix = ''
    if 'RoutingCodesMatrix' in inputData['flight'][0]: RoutingCodesMatrix = inputData['flight'][0]['RoutingCodesMatrix']
    ExtensionCodesMatrix = ''
    if 'ExtensionCodesMatrix' in inputData['flight'][0]: ExtensionCodesMatrix = inputData['flight'][0][
        'ExtensionCodesMatrix']

    ReturnRoutingCodesMatrix = ''
    if 'RoutingCodesMatrix' in inputData['Return']: ReturnRoutingCodesMatrix = inputData['Return']['RoutingCodesMatrix']
    ReturnExtensionCodesMatrix = ''
    if 'ExtensionCodesMatrix' in inputData['Return']: ReturnExtensionCodesMatrix = inputData['Return'][
        'ExtensionCodesMatrix']

    DepartingFrom = getStopPoint(inputData['flight'][0]['DepartingFrom'])
    Destination = getStopPoint(inputData['flight'][0]['Destination'])

    # await page.click('mat-tab-header div#mat-tab-label-0-0')  # RoundTrip
    await page.click('mat-tab-header div#mat-tab-group-0-label-0')  # RoundTrip


    # await page.wait_for_timeout(1001)
    await page.fill('matrix-location-field[formcontrolname="origin"] input', DepartingFrom)
    # await page.wait_for_timeout(1001)
    await page.fill('matrix-location-field[formcontrolname="dest"] input', Destination)

    # await page.wait_for_timeout(1001)
    await page.fill('mat-date-range-input .mat-start-date', date1)
    # await page.fill('mat-date-range-input .mat-start-date', '10/29/2023')
    await page.fill('mat-date-range-input .mat-end-date', date2)
    # await page.fill('mat-date-range-input .mat-end-date', '11/29/2023')
    # await page.wait_for_timeout(1001)

    if specifyTheDay1 in arr_date_modifier:
        specifyTheDay1 = arr_date_modifier[specifyTheDay1]
        await page.click('mat-select[formcontrolname="departureDateModifier"]')
        await page.click(
            'div.cdk-overlay-container div[role="listbox"] mat-option:nth-child(' + str(specifyTheDay1) + ')')
    if specifyTheDay2 in arr_date_modifier:
        specifyTheDay2 = arr_date_modifier[specifyTheDay2]
        await page.click('mat-select[formcontrolname="returnDateModifier"]')
        await page.click(
            'div.cdk-overlay-container div[role="listbox"] mat-option:nth-child(' + str(specifyTheDay2) + ')')

    if arrivalDeparture1 in arr_arrival_departure:
        arrivalDeparture1 = arr_arrival_departure[arrivalDeparture1]
        await page.click('mat-select[formcontrolname="departureDateType"]')
        await page.click('div.cdk-overlay-container mat-option[value="' + arrivalDeparture1 + '"]')
    if arrivalDeparture2 in arr_arrival_departure:
        arrivalDeparture2 = arr_arrival_departure[arrivalDeparture2]
        await page.click('mat-select[formcontrolname="returnDateType"]')
        await page.click('div.cdk-overlay-container mat-option[value="' + arrivalDeparture2 + '"]')

    # click = 0
    # if len(stopPoint1) > 0:
    #     click = 1
    #     await page.click('form matrix-flight-picker button.mdc-button--outlined')
    #     await page.fill('input[formcontrolname="routing"]', stopPoint1)
    # if len(stopPoint2) > 0:
    #     if click == 0:  await page.click('form matrix-flight-picker button.mdc-button--outlined')
    #     await page.fill('input[formcontrolname="routingRet"]', stopPoint2)

    await page.click('form matrix-flight-picker button.mdc-button--outlined')

    if RoutingCodesMatrix: await page.fill('input[formcontrolname="routing"]', RoutingCodesMatrix)
    if ExtensionCodesMatrix: await page.fill('input[formcontrolname="ext"]', ExtensionCodesMatrix)

    if ReturnRoutingCodesMatrix: await page.fill('input[formcontrolname="routingRet"]', ReturnRoutingCodesMatrix)
    if ReturnExtensionCodesMatrix: await page.fill('input[formcontrolname="extRet"]', ReturnExtensionCodesMatrix)

    PreferredTimes = 0xff
    if 'PreferredTimes' in inputData['flight'][0]: PreferredTimes = inputData['flight'][0]['PreferredTimes']
    if PreferredTimes != 0xff:
        await page.click('matrix-preferred-times button')
        # print('Prefferred---->')
        for j in range(6):
            if (PreferredTimes & (1<<j)) == 0:
                print('Preff---->', j + 1)
                preferred = page.locator('matrix-preferred-times mat-checkbox').nth(j)
                await preferred.click()



@app.route('/run', methods=['POST'])
async def run_matrix():
    # Получение списка аэропортов из тела запроса
    inputData = request.json.get('airports', [])

    print('=================>', inputData)
    async with async_playwright() as pw:
        print('Start')
        browser = await pw.chromium.launch(
            headless=False,
            # args = ["--start-maximized"]  # Запуск в полноэкранном режиме
            # args = ["--window-size=1280,1920"]  # Устанавливаем размер окна
        )

        x = datetime.now()  # Вызов метода now из класса datetime datetime.now().strftime("%X")

        start = time.time()
        print('connected ==> ', x.strftime("%x"), ' ', x.strftime("%X"))
        # print('connected ==> ',datetime.today())
        page = await browser.new_page()

        # ----------------------------------------
        # client = await page.context.new_cdp_session(page)
        # # Enable network and set blocked URLs
        # await client.send('Network.enable')
        # await client.send('Network.setBlockedURLs', {
        #     'urls': ['*.css*', '*.png*', '*.gif*']
        # })
        # ----------------------------------------

        # await page.wait_for_timeout(5000)
        print('goto')
        await page.set_viewport_size({"width": 1280, "height": 900})
        await page.goto('https://matrix.itasoftware.com/search', timeout=120000)
        title = await page.query_selector('mat-card-title.mat-mdc-card-title')
        print('title - ', await page.evaluate('title => title.textContent', title))

        # -------------------------------------
        if inputData['TripType'] == 'RoundTrip':
            if 'Return' in inputData:
                await inputParamsRoundTrip(page, inputData)
            else:
                await inputParamsRoundTripOld(page, inputData)


        elif inputData['TripType'] == 'OneWay':
            await inputParamsOneWay(page, inputData)
        else:
            err = await inputParamsMultiCity(page, inputData)

        await inputParamsCommon(page, inputData)

        # -------------------------------------

        await page.click('div.cdk-overlay-container mat-option')


        await page.wait_for_timeout(600000)
        return

if __name__ == '__main__':
    app.run(debug=True)
