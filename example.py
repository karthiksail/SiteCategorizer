from SiteReview import SiteReview 
import traceback
import csv

if __name__ == "__main__":
    sitereview = SiteReview()
    sitereview.InitTheBlueCoat() ## To Inital all the cookies need this function to call
    CsvRows = []
    with open("example_website.csv") as file:
        reader = csv.reader(file)
        for row in reader:
            CsvRows.append(row)
    result = []
    lengthCsv = len(CsvRows)
    counter = 0 
    try :   
        for row in CsvRows:
            status ,netloc,content = sitereview.BlueCoatGetSiteCategory(row[0])
            counter =counter+1
            row.append(netloc)
            if status == "OK":
                if "categorization" in content:  
                    for vals in content["categorization"]:
                        row.append(vals["name"])
                else:
                    row.append(str(content))
            else :
                row.append(str(content))
            result.append(row)
            print("\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t     ", end = "\r")
            print("Completed -  %.1f %% \t Last Result - %s" %((counter/lengthCsv * 100), str(row).replace("\n", ""))  ,end ="\r")
        sitereview.CloseBlueSuite()
    except Exception as  e :
        print(str(e))
        traceback.print_exc()
    finally:
        sitereview.CloseBlueSuite()
        with open("Output1.csv","w+") as file:
            csvWriter = csv.writer(file,delimiter=',')
            csvWriter.writerows(result)
