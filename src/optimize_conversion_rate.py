# offer_id    evt_name    evt_date    total_events    unique_customers
import argparse
import operator
import datetime

START_DATE = datetime.datetime.strptime('2016-05-07', "%Y-%m-%d").date()
END_DATE = datetime.datetime.strptime('2016-06-06', "%Y-%m-%d").date()
REC_LIMIT_FOR_DEBUG = 500000000000


def analyze_order_pv_mismatch(item_dict, purchased):
    items_purchased_without_views = 0
    for item_id in purchased:
        assert('order' in item_dict[item_id])
        if 'pv' not in item_dict[item_id] and \
                'ad_clk' not in item_dict[item_id] and \
            'eml_clk' not in item_dict[item_id] and \
                'mob_vw' not in item_dict[item_id]:
            # print item_dict[item_id].keys()
            items_purchased_without_views += 1

    return items_purchased_without_views


def get_item_dict(data_file):
    # creates a dictionary with items as key and list of events as values
    item_dict = {}
    with open(data_file) as df:
        for ln, line in enumerate(df):
            if ln == 0:
                continue
            if ln > REC_LIMIT_FOR_DEBUG:
                break

            record = line.split()

            if not record[0] in item_dict:
                item_dict[record[0]] = {}

            if not record[1] in item_dict[record[0]]:
                item_dict[record[0]][record[1]] = []

            evt_date = datetime.datetime.strptime(record[2], "%Y-%m-%d").date()
            event_info = {'evt_date': evt_date, 'total_events': int(
                record[3]), 'unique_customers': int(record[4])}
            item_dict[record[0]][record[1]].append(event_info)

    purchased, not_purchased = [], []
    for k in item_dict.keys():
        if 'order' in item_dict[k]:
            purchased.append(k)
        else:
            not_purchased.append(k)

    return item_dict, purchased, not_purchased


def get_conversion_rate(item_dict, purchased):
    conversion_rate = {}
    for item_id in purchased:
        order_events = item_dict[item_id]['order']
        tot_orders = 0
        for o_e in order_events:
            tot_orders += o_e['total_events']

        tot_uniq_views = 0
        if 'pv' in item_dict[item_id]:
            pv_events = item_dict[item_id]['pv']
            for pv_e in pv_events:
                tot_uniq_views += pv_e['unique_customers']
        if 'ad_clk' in item_dict[item_id]:
            pv_events = item_dict[item_id]['ad_clk']
            for pv_e in pv_events:
                tot_uniq_views += pv_e['unique_customers']
        if 'eml_clk' in item_dict[item_id]:
            pv_events = item_dict[item_id]['eml_clk']
            for pv_e in pv_events:
                tot_uniq_views += pv_e['unique_customers']
        if 'mob_vw' in item_dict[item_id]:
            pv_events = item_dict[item_id]['mob_vw']
            for pv_e in pv_events:
                tot_uniq_views += pv_e['unique_customers']

        if tot_uniq_views == 0:
            tot_uniq_views += tot_orders
        assert(tot_uniq_views > 0)

        conversion_rate[item_id] = float(tot_orders) / float(tot_uniq_views)

    return conversion_rate


def get_first_event_date(events):
    first_date = END_DATE
    first_event = None
    for evt in events:
        if evt['evt_date'] <= first_date:
            first_date = evt['evt_date']
            first_event = evt['evt_name']

    assert(first_event is not None)
    return first_date, first_event


def get_tot_activity_div_by_age(item_dict, not_purchased):
    uniq_view_div_by_age = {}
    for item_id in not_purchased:
        item_events = []
        for event_type in item_dict[item_id].keys():
            for evt in item_dict[item_id][event_type]:
                temp_dict = evt
                temp_dict['evt_name'] = event_type
                item_events.append(temp_dict)

        first_date, first_event = get_first_event_date(item_events)
        # print "First event: " + first_event
        approx_age = (END_DATE - first_date).days + 1
        assert(approx_age > 0)

        tot_uniq_views = 0
        for event_type in item_dict[item_id].keys():
            for evt in item_dict[item_id][event_type]:
                tot_uniq_views += evt['unique_customers']

        uniq_view_div_by_age[item_id] = float(
            tot_uniq_views) / float(approx_age)

    return uniq_view_div_by_age

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("data_file", help="path to data file")
    args = parser.parse_args()

    # creates a dictionary with items as key and list of events as values
    # PERFORMANCE: O(N), N = No. of records
    item_dict, purchased, not_purchased = get_item_dict(args.data_file)

    # analyze items with purchases but no page_views, ad_click, email_click,
    # mobile_view !!!
    items_purchased_without_views = analyze_order_pv_mismatch(
        item_dict, purchased)

    print "Total number of items: %d" % len(item_dict)
    print "Number of items that have been purchased: %d" % len(purchased)
    print "Purchased without page_views (ad_clk, eml_clk, mob_vw, pv): %d" % items_purchased_without_views

    # PERFORMANCE: O(N), N = No. of records
    # conversion rate for the purchased items
    conversion_rate = get_conversion_rate(item_dict, purchased)
    # total activity divided by the product age for the not purchased items
    tot_activity_div_by_age = get_tot_activity_div_by_age(
        item_dict, not_purchased)

    # PERFORMANCE: O(N Log N), N = No. of records
    # ranking for purchased items based on the conversion rate
    purchased_ranked = sorted(
        conversion_rate.items(), key=operator.itemgetter(1), reverse=True)
    # ranking for not purchased items based on the total activity divided by
    # their age
    not_purchased_ranked = sorted(
        tot_activity_div_by_age.items(), key=operator.itemgetter(1), reverse=True)

    print "\nPurchased 0:10: "
    for r in purchased_ranked[:10]:
        print r
    print "\nPurchased 400:410: "
    for r in purchased_ranked[400:410]:
        print r
    print "\nNot purchased 0:20: "
    for r in not_purchased_ranked[:20]:
        print r

    ranked = purchased_ranked + not_purchased_ranked
