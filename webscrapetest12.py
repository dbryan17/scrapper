import requests
from bs4 import BeautifulSoup
import psycopg2

headers = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36",
}
conn = ""

############################
######### TICK HELPER ######
############################

# optimized


def getUsers():
    cmd = 'select id from users'
    cur = conn.cursor()
    cur.execute(cmd)
    people = []
    for row in cur:
        people.append(row[0])
    return people


def getTick(str):
    things = str.split("·")
    if (len(things) <= 1):
        return (None, None, None, None)
    # things[1] is the entire content
    items = things[1].split(".")
    i = 0
    pitches = None
    type = None
    secondary = None
    notes = None
    while (len(items) > 0):
        item = items.pop(0)
        stripped = item.strip()
        # check if it is a pitches
        possPitches = item.split("pitches", 1)[0].strip()
        if (i == 0 and "pitches" in item and possPitches.isnumeric()):
            pitches = possPitches
        elif ("Solo" == stripped or "TR" == stripped or "Lead" == stripped or "Follow" == stripped or "Lead / Onsight" == stripped or "Lead / Flash" == stripped or "Lead / Redpoint" == stripped or "Lead / Fell/Hung" == stripped or "Lead / Pinkpoint" == stripped):
            if ("/" in stripped):
                types = stripped.split("/", 1)
                type = types[0].strip()
                secondary = types[1].strip()
            else:
                type = stripped
        # must be notes
        else:
            # the remainder of the string is the note, not just the split after the period
            notes = item
            while (len(items) > 0):
                itemTwo = items.pop(0)
                notes += "."
                notes += itemTwo
            notes = notes.replace("\n", " ")
            notes = notes.strip()
    if (notes == ""):
        notes = None
    return (pitches, type, secondary, notes)

############################
#### END TICK HELPER #######
############################


############################
######### AREAS ############
############################

def getArea(url, parent_id):

    elevation = None
    cords = None
    shared_by_user_url = None
    shared_on = None

    adminDbs = []

    id = url.split("/area/", 1)[1].split("/", 1)[0]

    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.content, "html.parser")

    descriptions = soup.find(class_="description-details")

    for cotent in descriptions:
        td = cotent.find("td")
        if (not isinstance(td, int)):
            if ("Elevation" in td.string):
                elevation = td.next_sibling.next_sibling.string
            elif ("GPS" in td.string):
                cords = td.next_sibling.next_sibling.contents[0].strip()
            elif ("Page Views" in td.string):
                views = td.next_sibling.next_sibling.string.split("t", 1)[
                    0].strip()
            elif ("Shared By" in td.string):
                shared_by_user_url = td.next_sibling.next_sibling.find("a")[
                    'href']
                shared_on = td.next_sibling.next_sibling.contents[2].split("on", 1)[
                    1].strip()
                # updates_url = td.next_sibling.next_sibling.find_all("a")[1]['href']
            elif ("Admins" in td.string):
                admins_tags = td.next_sibling.next_sibling.find_all("a")
                # this will get all but the last one which is updates
                for i in range(0, len(admins_tags) - 1):
                    adminDb = (admins_tags[i]['href'].split("user/", 1)
                               [1].split("/", 1)[0], id)
                    adminDbs.append(adminDb)

    # climbing area or bouldering outer area
    if ("Climbing in" in soup.title.string):
        area_name = soup.title.string.split("Climbing in", 1)[
            1].split(",", 1)[0].strip()

    # bouldering area with boulders
    elif ("Bouldering in" in soup.title.string):
        area_name = soup.title.string.split("Bouldering in", 1)[
            1].split(",", 1)[0].strip()

    descriptionAndGettingThere = soup.find_all(class_="fr-view")

    # best to just use .contents for these because they often contains links and other elemtns like line breaks
    description = []
    if (len(descriptionAndGettingThere) > 0):
        description = descriptionAndGettingThere[0].contents

    getting_there_with_links = []
    if (len(descriptionAndGettingThere) > 1):
        getting_there_with_links = descriptionAndGettingThere[1].contents

    real_getting_there = ""
    for line in getting_there_with_links:
        if (line.string):
            real_getting_there += line.string

    real_description = ""
    for line in description:
        if (line.string):
            real_description += line.string

    childern_areas_divs = soup.find_all("div", class_="lef-nav-row")

    children_areas = []

    for area_div in childern_areas_divs:
        children_areas.append(area_div.contents[1]['href'])

    classicsDbs = []
    classics_table = soup.find(
        "table", class_="table route-table hidden-xs-down")
    if (classics_table):
        classics_names = classics_table.find_all("strong")
        for name in classics_names:
            typess = name.parent.parent.parent.find(
                "span", class_="float-xs-right").next_sibling.next_sibling.string
            if (not ("Boulder" in typess or "Ice" in typess or "Mixed" in typess or "Snow" in typess)):
                # classics_links.append(name.parent['href'])
                classicsDbs.append((name.parent['href'].split(
                    "/route/", 1)[1].split("/", 1)[0], id))

    climbs_table = soup.find(id="left-nav-route-table")

    climbs_links = []
    # fucks it up if there are unsorted routes
    if (climbs_table):
        for climb_row in climbs_table.find_all("tr"):
            if (climb_row.find("a")):
                climbs_links.append(climb_row.find("a")['href'])

    # # when there is only one climb - its not a tr - in this cases, its the first <a> tag
    # if (climbs_table and len(climbs_links) == 1):
    #     climbs_links.append(climbs_table.find("a")['href'])

    # get the type of the area - either outer area, contains ice, contains bouldering, or contains
    # area_type = None
    # if (len(children_areas) > 0):
    #     area_type = "outer"
    # elif (soup.find("span", class_="route-type Ice") or soup.find("span", class_="route-type Mixed Ice")):
    #     area_type = "ice/mixed"
    # elif (soup.find("span", class_="route-type Boulder")):
    #     area_type = "boulder"
    # else:
    #     area_type = "rock"

    # # just throw it out if not rock route for the scope of this project
    # if (area_type == "boulder" or area_type == "mixed/ice"):
    #     print(id)
    #     return

    views = views.replace(",", "")
    views = int(views)

    if (elevation):
        elevation = elevation.split("ft", 1)[0].strip()
        elevation = elevation.replace(",", "")
        elevation = int(elevation)

    if (shared_by_user_url):
        shared_by_user_id = shared_by_user_url.split(
            "/user/", 1)[1].split("/", 1)[0]
        # add user to db
        if (shared_by_user_id not in getUsers()):
            getPeople(shared_by_user_url)
    else:
        shared_by_user_id = None

    dbObjArea = (id, area_name, real_description, real_getting_there,
                 parent_id, elevation, cords, shared_by_user_id, shared_on, views)

    # add area to db
    insert_area(dbObjArea)

    # either climbs are sub arreas - can't be both
    # but can just go through them both
    if (len(children_areas) != 0):

        for children_link in children_areas:
            getArea(children_link, id)

    else:
        # go throuh routes
        for route_link in climbs_links:
            getRoute(route_link, id)
    # if empty just nothing will happen

    # now that the area and all routes are added, we can add admins and classics
    for admin in adminDbs:
        insert_admin(admin)
    # pretty sure there's no way for this to trigger without going through all subareas and areas, so think we're fine to add with no checks
    # one way is if there is a classic boulder route thats in an outer area
    for classic in classicsDbs:
        insert_classic(classic)

    # print(dbObjArea)


############################
##### END AREAS ############
############################


############################
######### ROUTE ############
############################


def getRoute(url, area_id):

    id = url.split("/route/", 1)[1].split("/", 1)[0]
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.content, "html.parser")
    views = None
    shared_by_user_id = None

    try:
        possArr = soup.title.string.split(
            "Rock Climb")[1].split(",")
        if (len(possArr) > 2):
            name = (possArr[0] + possArr[1]).strip()
        else:
            name = possArr[0].strip()

    except:
        return

    # try the old tricks
    descriptions = soup.find(class_="description-details")

    for cotent in descriptions:
        td = cotent.find("td")
        if (not isinstance(td, int)):
            # correct
            nextNextSibling = td.next_sibling.next_sibling
            if ("Page Views" in td.string):
                views = nextNextSibling.string.split("t", 1)[
                    0].strip()
            elif ("Shared By" in td.string):
                # correct
                shared_by_user_url = nextNextSibling.find("a")[
                    'href']
                # correct
                shared_on = nextNextSibling.contents[2].split("on", 1)[
                    1].strip()
            elif ("Type" in td.string):
                str_arr = nextNextSibling.text.split(",")
                pitches = 1
                length = None
                types = []
                commitment_rating = 'I'
                while (len(str_arr) > 0):
                    curr = str_arr.pop()
                    if ("pitches" in curr):
                        pitches = curr.strip().split(" ", 1)[0]
                    elif ("ft" in curr):
                        length = curr.split("ft", 1)[0].strip()
                    elif ("Grade" in curr):
                        commitment_rating = curr.split("Grade")[1].strip()
                    else:
                        # must be types
                        # rest of str_arr is
                        types.append(curr.strip())
                        for t in str_arr:
                            types.append(t.strip())
                        break
                # throw out non rock climbs this way now
                if ("Boulder" in types or "Ice" in types or "Mixed" in types or "Snow" in types):
                    return
            elif ("FA" in td.string):
                if (nextNextSibling):
                    if (nextNextSibling.string):
                        fa = nextNextSibling.string.strip()
                    else:
                        fa = "unknown"
                else:
                    fa = "unkown"

    # CAN ALSO DO THIS FOR ALL GRADING TYPES
    yds_grade = soup.find("h2", class_="inline-block mr-2").find("span",
                                                                 class_="rateYDS").contents[0].strip()

    danger_rating = None
    aid_rating = None

    # If it is an aid route, the aid rating is here
    grades = soup.find("h2", class_="inline-block mr-2")
    if (grades.contents[len(grades) - 1].string):
        mystery_rating = grades.contents[len(grades) - 1].strip()
    else:
        mystery_rating = "G/PG"

    count = types.count("Aid")
    if (count >= 1):
        aid_rating = mystery_rating
        if (len(aid_rating.split(" ")) > 1):
            danger_rating = aid_rating.split(" ", 1)[1].strip()
            aid_rating = aid_rating.split(" ", 1)[0].strip()
    else:
        danger_rating = mystery_rating

    stats_link = soup.find("a", title="View Stats")['href']

    descriptionAndGettingThereAndPro = soup.find_all(class_="fr-view")

    description = None
    location = None
    pro = None
    while len(descriptionAndGettingThereAndPro) > 0:
        curr = descriptionAndGettingThereAndPro.pop(0)
        dgorp = curr.parent.find("h2").contents[0].strip()
        if ("Description" in dgorp):
            description = ""
            for line in curr.contents:
                if (line.string):
                    description += line.string
        elif ("Location" in dgorp):
            location = ""
            for line in curr.contents:
                if (line.string):
                    location += line.string
        elif ("Protection" in dgorp):
            pro = ""
            for line in curr.contents:
                if (line.string):
                    pro += line.string

    if (length):
        length = int(length)
    pitches = int(pitches)
    views = views.replace(",", "")
    views = int(views)

    shared_by_user_id = shared_by_user_url.split(
        "/user/", 1)[1].split("/", 1)[0]

    if (shared_by_user_id not in getArea()):
        # add it
        getPeople(shared_by_user_url)

        # same as for the database
    dbObjRoute = (id, name, area_id, description, location, pro, yds_grade, danger_rating,
                  aid_rating, commitment_rating, length, pitches, fa, shared_by_user_id, shared_on, views)
    insert_route(dbObjRoute)

    for type in types:
        TypeDb = (id, type)
        insert_type(TypeDb)

        # print((id, type))

    getStats(id, stats_link)


############################
######## END  ROUTE ########
############################


############################
######### STATS ############
############################

def getStats(route, url):
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.content, "html.parser")

    #starsAndPeople = []
    #gradesAndPeople = []
    #todoers_links = []
    #ticks = []

    # we want all diffcilty and danger ratings, all ticks, all star ratings, and todos

    # star ratings

    # the h3s are star ratings table header, suggested raitn header,  todos header, ticks header
    contents = soup.find_all("h3")

    for content in contents:
        if ("Star Ratings" in content.text):
            #starsAndPeople = []
            # CAN ALSO GET ACTUAL AVERAGE FROM HERE, BUT MIGHT BE BEST TO STICK TO PUBLIC USERS
            # total_with_private = content.text.split("Ratings", 1)[1].strip()
            star_raters = content.next_sibling.next_sibling.find_all("a")
            # total_public = len(star_raters)
            for star_rater in star_raters:
                star_rater_link = star_rater['href']
                # only given in star images, so need to count this way
                # TODO make sure this works for bomb ratings - should be zero
                stars = len(
                    star_rater.parent.next_sibling.next_sibling.find_all("img"))
                if (stars == 1):
                    # check if it is a bomb
                    if ("bomb" in star_rater.parent.next_sibling.next_sibling.find(
                            "img")['src']):
                        stars = 0
                dbStar = (star_rater_link.split("user/", 1)
                          [1].split("/", 1)[0], route, stars)
                insert_star(dbStar)
                # add to database here
                # starsAndPeople.append(dbStar)
                # rating = len(rating_outer.find_all("img"))
        elif ("On To-Do Lists" in content.text):
            # this matches below - will it always be like that??/
            todoers_outer = content.next_sibling.next_sibling.find_all("a")
            #todoers_links = []
            for todoer_outer in todoers_outer:
                todoer = todoer_outer['href'].split(
                    "user/", 1)[1].split("/", 1)[0]
                dbTodo = (todoer, route)

                # todoers_links.append(dbTodo)
                insert_todo(dbTodo)
        elif ("Suggested Ratings" in content.text):
            # this matches below - always?????
            # rated_with_private = content.text.split("Ratings", 1)[1].strip()
            # gradesAndPeople = []
            raters = content.next_sibling.next_sibling.find_all("a")
            # total_rater_public = len(raters)
            for rater in raters:
                rater_link = rater['href']
                danger_rating = None
                aid_rating = None
                full_rating = rater.parent.next_sibling.next_sibling.string
                if (len(full_rating.split(" ", 1)) > 1):
                    # messing up here becuase "easy 5th"
                    if ("asy" in full_rating):
                        grade_rating = "Easy 5th"
                        if (len(full_rating.strip().split("5th", 1)[1]) > 0):
                            danger_rating = full_rating.split("5th", 1)[
                                1].strip()
                            if (danger_rating != "PG13" and danger_rating != "R" and danger_rating != "X"):
                                aid_rating = danger_rating
                                danger_rating = None
                        else:
                            danger_rating = "G/PG"
                    else:
                        grade_rating = full_rating.split(" ", 1)[0]
                        danger_rating = full_rating.split(" ", 1)[1]
                        aid_rating = None
                        if (danger_rating != "PG13" and danger_rating != "R" and danger_rating != "X"):
                            aid_rating = danger_rating
                            if (len(aid_rating.split(" ")) > 1):
                                danger_rating = aid_rating.split(" ")[
                                    1].strip()
                                aid_rating = aid_rating.split(" ")[
                                    0].strip()
                            else:
                                danger_rating = None
                else:
                    grade_rating = full_rating
                    danger_rating = "G/PG"
                # could have someone who didn't add a grade rating
                if (not ("C" in grade_rating or "A" in grade_rating or "X" in grade_rating or "PG13" in grade_rating or "R" in grade_rating)):
                    dbRate = (rater_link.split(
                        "user/", 1)[1].split("/", 1)[0], route, grade_rating, danger_rating, aid_rating)
                    # gradesAndPeople.append(dbRate)
                    insert_rating(dbRate)

                # else:
                #     grade_rating = full_rating
                #     danger_rating = "G/PG"
                #     dbRate = (rater_link.split(
                #         "user/", 1)[1].split("/", 1)[0], route, grade_rating, None, None)
                #     # gradesAndPeople.append(dbRate)
                #     insert_rating(dbRate)
        # tick has person, date, style, secondary style, pitches, notes
        elif ("Ticks" in content.text):
            #ticks = []
            # total_ticks_with_private = content.text.split("Ticks", 1)[
            # 1].strip()
            tickers = content.next_sibling.next_sibling.find_all("a")
            for ticker in tickers:
                ticker_person_url = ticker['href']
                ticker_person_id = ticker_person_url.split(
                    "/user/", 1)[1].split("/")[0]
                dates = ticker.parent.next_sibling.next_sibling.find_all(
                    "strong")
                # each person can tick multiple times
                for date in dates:
                    real_date = date.text
                    if (real_date.strip() == "-no date-"):
                        real_date = None
                    tick = getTick(date.next_sibling)
                    dbTick = ((ticker_person_id,
                              route, real_date) + tick)
                    # ticks.append(dbTick)
                    insert_tick(dbTick, False)

    # now need to deal with private ticks
    privates_outer_poss = soup.find_all(class_="small text-muted")
    for poss in privates_outer_poss:
        if (poss.text == "No names/notes"):
            private_outer = poss.parent.next_sibling.next_sibling.find_all(
                "strong")
            for private in private_outer:

                if (private.text.strip() == "-no date-"):
                    date = None
                else:
                    date = private.text

                dbTick = ((route, date))
                #ticks.append((None, private.text, None, None, None, None))
                insert_tick(dbTick, True)

    # print("____")
    # print(starsAndPeople)
    # print("____")
    # print(gradesAndPeople)
    # print("____")
    # print(todoers_links)
    # print("____")
    # print(ticks)

############################
######### END STATS ########
############################


############################
######### USERS ############
############################

def getPeople(url):
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.content, "html.parser")

    id = url.split("/user/", 1)[1].split("/", 1)[0]

    display_name = soup.title.text.split(" on ", 1)[0]
    begin = soup.find("div", class_="info mt-1")
    start_date = begin.contents[3].text
    points = begin.find(class_="mt-1").contents[1].text.split(" ", 1)[0]

    pi_contents = soup.find(
        "h2", class_="dont-shrink mb-0").next_sibling.next_sibling.contents

    # TODO this is where you find where they are from and gender and age - kinda anyoing becuae
    # people could ahve any one of the three and there messily thrown in a div
    age = None
    i = 0

    for pi in pi_contents:
        if ("·" not in pi.text and i == 0):
            if (pi.text.strip() != ""):
                if ("years old" in pi.text.strip()):
                    age = pi.text.strip().split("years old", 1)[0]
                    break
        if ("·" in pi.text):
            split_arr = pi.text.strip().split("·")
            if ("years old" in split_arr[0]):
                age = split_arr[0].split("years old", 1)[0]
                break
        i += 1

    # fav_climbs_string = None
    other_interests_string = None
    bios = soup.find_all("div", class_="bio-detail")
    for bio in bios:
        strong = bio.find("strong")
        if (strong):
            if ("Other Interests" == strong.text):
                other_interests_string = bio.contents[3].text

    points = points.replace(",", "")
    points = int(points)

    if (start_date.strip() == "-no date-"):
        start_date = None

    dbObjUser = (id, display_name, start_date, age,
                 other_interests_string, points)
    insert_user(dbObjUser)


############################
######### END USERS ########
############################


def insert_user(dbObjUser):

    try:
        curr = conn.cursor()
        insert = """INSERT INTO users VALUES (%s, %s, %s, %s, %s, %s)"""
        curr.execute(insert, dbObjUser)
        # insert user into done array
        # inserted_users_ids.append(dbObjUser[0])
    except (Exception, psycopg2.Error) as error:
        print("Failed to insert record into users table", error)
        curr.close()
        conn.cancel()
        # exit()
    finally:
        conn.commit()


def insert_admin(dbObjAdmin):

    if (dbObjAdmin[0] not in getUsers()):
        # insert it so we have foriegn key
        getPeople("https://www.mountainproject.com/user/" +
                  dbObjAdmin[0] + "/")

    try:
        curr = conn.cursor()
        insert = """INSERT INTO admins_areas VALUES (%s, %s)"""
        curr.execute(insert, dbObjAdmin)
    except (Exception, psycopg2.Error) as error:
        print("Failed to insert record into admins table", error)
        curr.close()
        conn.cancel()
        # exit()
    finally:
        conn.commit()


def insert_classic(dbClassicObj):
    # what can happen is a boulder classic in an outer area - would throw this off - in this case just throw it out but canceliing on a caught error
    try:
        curr = conn.cursor()
        insert = """INSERT INTO classics VALUES (%s, %s)"""
        curr.execute(insert, dbClassicObj)
    except (Exception, psycopg2.Error) as error:
        conn.rollback()
        curr.close()
        conn.cancel()
        print("Failed to insert record into classics table", error)
    finally:
        conn.commit()


def insert_route(dbObjRoute):
    try:
        curr = conn.cursor()
        insert = """INSERT INTO routes VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        curr.execute(insert, dbObjRoute)
    except (Exception, psycopg2.Error) as error:
        print("Failed to insert record into routes table", error)
        curr.close()
        conn.cancel()
        # exit()
    finally:
        conn.commit()


def insert_area(dbObjArea):
    try:
        curr = conn.cursor()
        insert = """INSERT INTO areas VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        curr.execute(insert, dbObjArea)
    except (Exception, psycopg2.Error) as error:
        print("Failed to insert record into areas table", error)
        curr.close()
        conn.cancel()
        # exit()
    finally:
        conn.commit()


def insert_type(typeObj):
    try:
        curr = conn.cursor()
        insert = """INSERT INTO route_types VALUES (%s, %s)"""
        curr.execute(insert, typeObj)
    except (Exception, psycopg2.Error) as error:
        print("Failed to insert record into types table", error)
        curr.close()
        conn.cancel()
        # exit()
    finally:
        conn.commit()


def insert_star(dbObjStar):
    if (dbObjStar[0] not in getUsers()):
        # insert it so we have foriegn key
        getPeople("https://www.mountainproject.com/user/" +
                  dbObjStar[0] + "/")

    try:
        curr = conn.cursor()
        insert = """INSERT INTO star_ratings VALUES (%s, %s, %s)"""
        curr.execute(insert, dbObjStar)
    except (Exception, psycopg2.Error) as error:
        print("Failed to insert record into stars table", error)
        curr.close()
        conn.cancel()
        # exit()
    finally:
        conn.commit()


def insert_todo(dbTodo):
    if (dbTodo[0] not in getUsers()):
        # insert it so we have foriegn key
        getPeople("https://www.mountainproject.com/user/" +
                  dbTodo[0] + "/")

    try:
        curr = conn.cursor()
        insert = """INSERT INTO todos VALUES (%s, %s)"""
        curr.execute(insert, dbTodo)
    except (Exception, psycopg2.Error) as error:
        print("Failed to insert record into todos table", error)
        curr.close()
        conn.cancel()
        # exit()
    finally:
        conn.commit()


def insert_rating(dbRate):
    if (dbRate[0] not in getUsers()):
        # insert it so we have foriegn key
        getPeople("https://www.mountainproject.com/user/" +
                  dbRate[0] + "/")

    try:
        curr = conn.cursor()
        insert = """INSERT INTO difficulty_ratings VALUES (%s, %s, %s, %s, %s)"""
        curr.execute(insert, dbRate)
    except (Exception, psycopg2.Error) as error:
        print("Failed to insert record into ratings table", error)
        curr.close()
        conn.cancel()
        # exit()
    finally:
        conn.commit()


def insert_tick(dbTick, private):
    if (not private):
        if (dbTick[0] not in getUsers()):
            # insert it so we have foriegn key
            getPeople("https://www.mountainproject.com/user/" +
                      dbTick[0] + "/")

        try:
            curr = conn.cursor()
            insert = """INSERT INTO ticks (user_id, route_id, date, pitches, style, secondary_style, notes) VALUES (%s, %s, %s, %s, %s, %s, %s)"""
            curr.execute(insert, dbTick)
        except (Exception, psycopg2.Error) as error:
            print("Failed to insert record into ticks table", error)
            curr.close()
            conn.cancel()
            # exit()
        finally:
            conn.commit()
    else:
        try:
            curr = conn.cursor()
            insert = """INSERT INTO ticks (route_id, date) VALUES (%s, %s)"""
            curr.execute(insert, dbTick)
        except (Exception, psycopg2.Error) as error:
            print("Failed to insert record into ticks table", error)
            curr.close()
            conn.cancel()
            # exit()
        finally:
            conn.commit()


############################
#### CONNECT DB ############
############################


def connect_db():

    # read the password file
    try:
        # password file should be in a secure location
        pwd_file = open('.pwd')
    except OSError:
        print("Error: No authorization")
        exit()

        # what can go wrong?
    try:
        conn = psycopg2.connect(
            dbname="dfbrya19_final",
            user="dfbrya19",
            password=pwd_file.readline(),
            host="ada.hpc.stlawu.edu"
        )
    except psycopg2.Error:
        print("Error: cannot connect to database")
        exit()
    finally:
        pwd_file.close()

    return conn


# if this file is being run as a program and *not* imported as a module
if __name__ == "__main__":

    conn = connect_db()

    # get all users and add to inserted users so we can do this in chunks
    # instead -- sanitize the inputs
    cmd = 'select id from users'

    # a cusor is an object for issuing sql commands to a connection
    cur = conn.cursor()
    cur.execute(cmd)
    # for row in cur:
    #     inserted_users_ids.append(row[0])

    # Only need this when we stopped halfway through an area to make it more effiecent
    cmd = 'select id from areas'
    cur = conn.cursor()
    cur.execute(cmd)
    # for row in cur:
    #     old_areas.append(row[0])

    #getArea("https://www.mountainproject.com/area/112488272/northwest", None)

    outer_areas = ["https://www.mountainproject.com/area/105907743/international"
                   ]
    # , ,
    #         "https://www.mountainproject.com/area/105891603/vermont", "https://www.mountainproject.com/area/105800424/new-york", "https://www.mountainproject.com/area/106598130/north-dakota", "https://www.mountainproject.com/area/105948977/maine", "https://www.mountainproject.com/area/105872225/new-hampshire"]

    #getArea("https://www.mountainproject.com/area/106343403/oahu", None)
    # getArea("https://www.mountainproject.com/area/106457411/mokuleia-wall", None)
    # getArea("https://www.mountainproject.com/area/118689884/slot-canyon", 118689852)
    for area in outer_areas:
        getArea(area, None)
    # getRoute(
    #     "view-source:https://www.mountainproject.com/route/106286285/altered-scale", 105868013)

    # getRoute(
    #     "https://www.mountainproject.com/route/106099503/short-mans-sorrow", 106523681)
    # getArea("https://www.mountainproject.com/area/106219126/cedar-rock", None)
    # getArea("https://www.mountainproject.com/area/106457411/mokuleia-wall", None)
    #getRoute("https://www.mountainproject.com/route/121210278/sistine-grapple", None)
    # getArea(
    #     "https://www.mountainproject.com/area/106360444/palisades-kepler-state-park", None)

    # works! sorta - at least complete
    # getArea("https://www.mountainproject.com/area/108682712/dog-boy-village", None)
    # getArea("https://www.mountainproject.com/area/111721391/florida", None)
    # getRoute("https://www.mountainproject.com/route/108209443/bouncer", None)
    # getArea("https://www.mountainproject.com/area/121920042/sunrise-notch", None)
    # getPeople("https://www.mountainproject.com/user/200649777/aidan-hagerty")
    # getRoute("https://www.mountainproject.com/route/105924807/the-nose", None)
    # getRoute("https://www.mountainproject.com/route/106103545/golden-girl", None)
    # getRoute("https://www.mountainproject.com/route/112146817/up-your-bum", None)
    # getArea("https://www.mountainproject.com/area/107123406/south-colton", None)

    # this is a user with weird pi
    # https://www.mountainproject.com/user/107162710/jeremy-o


# def getComments(url):
#     page = requests.get(url)
#     soup = BeautifulSoup(page.content, "html.parser")

#     pages_list = soup.find_all("a", class_="no-click")
#     pages = int(pages_list[len(pages_list) - 1].text.split("of", 1)[1].strip())

#     route_comments = []
#     area_comments = []
#     for i in range(1, pages + 1):

#         if (i == 1):
#             URL = "https://www.mountainproject.com/user/107548455/benjamin-brooke/comments"
#             page = requests.get(URL)
#             soup = BeautifulSoup(page.content, "html.parser")
#         else:
#             URL = "https://www.mountainproject.com/user/107548455/benjamin-brooke/comments" + \
#                 "?page=" + str(i)
#             page = requests.get(URL)
#             soup = BeautifulSoup(page.content, "html.parser")

#         comment_rows = soup.find_all("tr", class_="comment-row")
#         for comment_row in comment_rows:
#             link = comment_row.find("strong").find("a")['href']
#             comment_date = comment_row.find(
#                 "div", class_="float-xs-right text-warm small mt-half").text.strip()
#             comment_text = comment_row.find(
#                 "span", class_="new-indicator").next_sibling.strip()
#             if ("/route/" in link):
#                 # comment on a route
#                 route_comments.append((link, comment_date, comment_text))

#             elif ("/area/" in link):
#                 # comment on an area
#                 area_comments.append((link, comment_date, comment_text))

#     print("______")
#     print(route_comments)
#     print("______")
#     print(area_comments)


###### NOTE s #########
"""

done areas:
"https://www.mountainproject.com/area/106316122/hawaii", "https://www.mountainproject.com/area/111721391/florida",
                   "https://www.mountainproject.com/area/106861605/delaware",
                   "https://www.mountainproject.com/area/112389571/indiana", "https://www.mountainproject.com/area/106092653/iowa", "https://www.mountainproject.com/area/107235316/kansas"
"https://www.mountainproject.com/area/106842810/rhode-island", "https://www.mountainproject.com/area/107638915/south-carolina", "https://www.mountainproject.com/area/105798164/in-progress
"https://www.mountainproject.com/area/105891603/vermont", "https://www.mountainproject.com/area/105800424/new-york",
"https://www.mountainproject.com/area/105872225/new-hampshire", "https://www.mountainproject.com/area/105948977/maine"
part way done :
"https://www.mountainproject.com/area/105873282/north-carolina" - good chunk left 
"https://www.mountainproject.com/area/105868674/kentucky" - lietarlly only a couple climbs in roadsie aren't done

"""
