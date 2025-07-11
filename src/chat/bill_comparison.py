def compare_bills(bills):
    if len(bills) < 4:
        return "Not enough bills to compare."

    last_four_bills = bills[-4:]
    comparison_results = {}

    for i in range(1, len(last_four_bills)):
        previous_bill = last_four_bills[i - 1]
        current_bill = last_four_bills[i]
        comparison_results[f'Comparison between Bill {i} and Bill {i + 1}'] = {
            'Previous Bill Amount': previous_bill['amount'],
            'Current Bill Amount': current_bill['amount'],
            'Difference': current_bill['amount'] - previous_bill['amount']
        }

    return comparison_results