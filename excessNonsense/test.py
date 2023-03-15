cards = 220
views = {f'view {i+1}': [] for i in range((cards / 21).__ceil__())}

for view in range(len(views)):
    if len(views) == 1: break
    
    # First view in array
    if len(views) - view - 1 == 0: views[f'view {len(views) - view}'] = ['Next Page']
    
    # Last view in array
    elif len(views) - view - 1 == len(views) - 1: views[f'view {len(views) - view}'] = ['Prev Page']
    
    # Any other view in array
    else: views[f'view {len(views) - view}'] = ['Prev Page', 'Next Page']

print(views)