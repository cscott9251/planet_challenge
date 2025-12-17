from find_best_opportunity import opportunities_pipeline




if __name__ == "__main__":

    start_date = "2024-11-07"
    #end_date = "2022-10-10"
    window = 7 # write one less because of starting from 0
    
    opportunities_pipeline(start_date, window)