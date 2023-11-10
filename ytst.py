# *imported libraries*
import streamlit as st
import pandas as pd
import pymongo
import mysql.connector
import googleapiclient.discovery
from googleapiclient.discovery import build

# **connecting string to connect with google api

api_service_name ="youtube"
api_version = "v3"
api_key='AIzaSyCqlHxHz4r8wR0_vOa4xqbjZnwH9khj3Es'
youtube = build(api_service_name,api_version,developerKey=api_key)



st.title('**:green[YOUTUBE CHANNEL DATA HARVESTING AND WAREHOUSING]**')

# ***Define function to get channel id***
def get_channel_id():
    if not user_input:
        st.error("Please enter a valid channel name.")
        return None

    request = youtube.search().list(
        part='id,snippet',
        q=user_input,
        channelType='any',
        maxResults=1
    )

    try:
        response = request.execute()
        # Check if the expected keys exist in the response
        if 'items' in response and response['items']:
            channel_id = response['items'][0]['snippet'].get('channelId')
            if channel_id:
                return channel_id
            else:
                st.error("Channel ID not found in the API response.")
                return None
        else:
            st.error("Please Enter The Channel Name")
            return None
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return None
    
# ***Define function to get channel details***
def channel_details(chnl_id):
    request = youtube.channels().list(
             part="snippet,contentDetails,statistics",
             id=chnl_id
        )
    response = request.execute()

    dic =  dict(tit = response['items'][0]['snippet']['title'],
                chnl_id = response['items'][0]['id'],
                des = response['items'][0]['snippet']['description'],
                pub = response['items'][0]['snippet']['publishedAt'].replace('Z', '').replace('T', ' '),
                sbc = response['items'][0]['statistics']['subscriberCount'],
                vic = response['items'][0]['statistics']['videoCount'],
                vwc = response['items'][0]['statistics']['viewCount'],
                ply_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads'])
    return dic

# ***Define function to get playlist details
def pl (chnl_id):

 request = youtube.playlists().list(
        part="snippet,contentDetails",
        channelId=chnl_id,
        maxResults=50
    )
 plylst = request.execute()

 playlists = []

 for playlist_item in plylst.get('items', []):
        playlist_info = {
            'chnl_id': playlist_item['snippet']['channelId'],
            'plylst_id': playlist_item['id'],
            'Itcnt': playlist_item['contentDetails']['itemCount'],
            #'kind': playlist_item['kind'],
            #'chtit': playlist_item['snippet']['channelTitle'],
            'vidtit': playlist_item['snippet']['title'],
            'publidate': playlist_item['snippet']['publishedAt'].replace('Z', '').replace('T', ' '),
            'videsc': playlist_item['snippet']['localized']['description']
        }
        playlists.append(playlist_info)

 return playlists

# ***Define function to get video ids
def vididdetl(playlist_id):
  Videoids = []
  next_page_token = None


  while True:
    request = youtube.playlistItems().list(
          part="snippet,contentDetails",
          playlistId=playlist_id,
          maxResults=50,
          pageToken=next_page_token
      )
    response = request.execute()



    for VidIds in response.get('items',[]):
        Video_ids =  VidIds['contentDetails']['videoId']

        Videoids.append(Video_ids)

    next_page_token = response.get('nextPageToken')

    if not next_page_token:
            break

  return Videoids

# ***Define function to get video details
def videodetls(videoids):
    videdetls = []
    for i in videoids:
        request = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=i,
            maxResults=50
        )
        response = request.execute()

        

        for Viddats in response.get('items', []):
            Videodata = {
                "channel_name": Viddats['snippet']['channelTitle'],
                "channel_id": Viddats['snippet']['channelId'],
                "vidtit": Viddats['snippet']['title'],
                "videoids": Viddats['id'],
                "viddes": Viddats['snippet']['description'],
                "vidpblsd": Viddats['snippet']['publishedAt'].replace('Z', '').replace('T', ' '),
                "viddurtin": Viddats['contentDetails']['duration'],
                "vidviwcnt": Viddats['statistics']['viewCount'],
                "vidliks": Viddats['statistics'].get('likeCount', 'NA'),
                "vidfavcnt": Viddats['statistics']['favoriteCount'],
                "vidcmntcnt": Viddats['statistics'].get('commentCount', 'NA')

            }

            videdetls.append(Videodata)

    return videdetls

# ***Define function to get comment details
def cmntdetls(videoids):
  CmntDetls = []
  for i in videoids:

    request = youtube.commentThreads().list(
      part="snippet,replies",
      videoId = i,
      maxResults=2
      )
    response = request.execute()
    try:



      for Comment in response['items']:
        Comment_details = { 'channel_id':Comment['snippet']['channelId'],
                            'video_id' : Comment['snippet']['videoId'],
                            'comment' : Comment['snippet']['topLevelComment']['snippet'].get('textOriginal','NA'),
                            'author_name' : Comment['snippet']['topLevelComment']['snippet'].get('authorDisplayName','NA'),
                            'authorchnlid': Comment['snippet']['topLevelComment']['snippet']['authorChannelId'].get('value','NA'),
                            'cmntrply'  :   Comment['snippet'].get('totalReplyCount',0),
                            'publishdate':  Comment['snippet']['topLevelComment']['snippet'].get('publishedAt','NA').replace('Z', '').replace('T', ' ')}

        CmntDetls.append(Comment_details)
    except:
      pass


  return CmntDetls

# ***Main Define function to get all datas of a channel***
def youtube_chnl_details():
      if user_input:  
        chnl_id=get_channel_id()
        if chnl_id:
            chnldetls=channel_details(chnl_id)
            playlistdetails=pl (chnl_id)
            videoiddtls=vididdetl(chnldetls['ply_id'])
            videoids = videoiddtls
            videodetails=videodetls(videoids)
            commentdtls = cmntdetls(videoids)

            youtubechnldata =  {'channel_details':chnldetls,
                                'play_list' : playlistdetails,
                                'video_datas' : videodetails,
                                'comment_details':commentdtls}

            return youtubechnldata


def get_channelname_in_mongo():

        youtubemongo=pymongo.MongoClient("mongodb+srv://rkreddy4895:Rkr2298@rkreddy.nn8dtc8.mongodb.net/?retryWrites=true&w=majority")

        ytdata=youtubemongo["youtubechanneldata"]

        coll=ytdata["youtube_chnl_details"]



        channel_names = []

        # Query to retrieve all documents in the collection
        documents = coll.find()

 
    # Iterate over the documents and extract the value of the specified key
        for document in documents:
            keys = "channel_details.tit".split('.')
            value = document
            for key in keys:
                if key in value:
                    value = value[key]
                else:
                    print(f"Key 'channel_details.tit' not found in document ID: {document['_id']}")
                    break
            else:
                channel_names.append(value)

        return channel_names


# *Define function to view datas from MongoDB*

def get_video_datas(): 
        youtubemongo=pymongo.MongoClient("mongodb+srv://rkreddy4895:Rkr2298@rkreddy.nn8dtc8.mongodb.net/?retryWrites=true&w=majority")
                
        ytdata=youtubemongo["youtubechanneldata"]

        coll=ytdata["youtube_chnl_details"]
        
        channel_names=get_channelname_in_mongo()

        select_channel = st.selectbox(
                            'Select The channel name',
                            ('select the channel ',) + tuple(channel_names))
        
        if select_channel:
           query = {"channel_details.tit": select_channel}

           datainmongo = coll.find_one(query)
           if datainmongo:
            return dict(datainmongo)
           else:
            st.warning("No data found select the channel you want to view.")
            return None
        else:
            return None

# *Define function to select channelname for sql

def select_channel():
        youtubemongo=pymongo.MongoClient("mongodb+srv://rkreddy4895:Rkr2298@rkreddy.nn8dtc8.mongodb.net/?retryWrites=true&w=majority")
        
        ytdata=youtubemongo["youtubechanneldata"]

        coll=ytdata["youtube_chnl_details"]

        channel_names = get_channelname_in_mongo()

        select_channel = st.selectbox(
                'Select The channel name',
                ('select the channel ',) + tuple(channel_names))

        query = {"channel_details.tit": select_channel}
        mongodata = coll.find_one(query)
        return mongodata    

               

# *Define function to migrate data in SQL

def data_storein_sql():                      
        #if select_channel:
            conn = mysql.connector.connect(host='localhost',user='root',password='Rkr2298',autocommit=True,auth_plugin='mysql_native_password',charset="utf8mb4")
            mycursor=conn.cursor()

            mycursor.execute("CREATE DATABASE IF NOT EXISTS Youtubechanneldetails")


            mycursor.execute("USE Youtubechanneldetails")


            mycursor.execute("""CREATE TABLE IF NOT EXISTS channel_data (channel_name VARCHAR(100), channel_id VARCHAR(100), channel_description TEXT, published_at DATETIME, video_count INT, channel_views INT, channel_subscribers INT, playlist_id VARCHAR(50))""")
            mycursor.execute("""CREATE TABLE IF NOT EXISTS playlist_data (channel_id VARCHAR(50), playlist_id VARCHAR(100), playlist_title VARCHAR(100), playlist_itemcount INT, publisheddate VARCHAR(100), playlist_description LONGTEXT)""")
            mycursor.execute("""CREATE TABLE IF NOT EXISTS video_data (channel_name VARCHAR(100), channel_id VARCHAR(100), video_title VARCHAR(100), video_id VARCHAR(50), video_description LONGTEXT, video_published VARCHAR(100), video_duration VARCHAR(100), video_viewcount BIGINT, video_likes INT, video_favourite INT, video_comment INT )""")
            mycursor.execute ("""CREATE TABLE IF NOT EXISTS comment_data (channel_id VARCHAR(100), video_id VARCHAR(100), comment TEXT, author_name VARCHAR(100), authorchnlid VARCHAR(100), cmntrply VARCHAR(100), publishdate VARCHAR(100))""")

            
            mongoytdata = select_channel()    
            if mongoytdata:  
                insert_channel_sql = """INSERT INTO channel_data (channel_name, channel_id, channel_description, published_at, video_count, channel_views, channel_subscribers, playlist_id)VALUES (%s, %s, %s, %s, %s, %s, %s,%s)"""
                channel_data = (mongoytdata['channel_details']['tit'],
                                mongoytdata['channel_details']['chnl_id'],
                                mongoytdata['channel_details']['des'],
                                mongoytdata['channel_details']['pub'],
                                mongoytdata['channel_details']['vic'],
                                mongoytdata['channel_details']['vwc'],
                                mongoytdata['channel_details']['sbc'],
                                mongoytdata['channel_details']['ply_id'])
                mycursor.execute(insert_channel_sql, channel_data)


                for playlist in mongoytdata['play_list']:
                    insert_playlist_sql = """INSERT INTO playlist_data (channel_id, playlist_id, playlist_title, playlist_itemcount, publisheddate, playlist_description)VALUES (%s, %s, %s, %s, %s, %s)"""
                    playlist_data = (playlist['chnl_id'],
                                    playlist['plylst_id'],
                                    playlist['vidtit'],
                                    playlist['Itcnt'],
                                    playlist['publidate'],
                                    playlist['videsc'])
                    mycursor.execute(insert_playlist_sql, playlist_data)



                for videodetails in mongoytdata['video_datas']:
                    insert_video_sql = """INSERT INTO video_data (channel_name, channel_id, video_title, video_id, video_description, video_published, video_duration, video_viewcount, video_likes, video_favourite, video_comment) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s )"""
                    viddats=(videodetails['channel_name'], 
                            videodetails['channel_id'], 
                            videodetails['vidtit'], 
                            videodetails['videoids'], 
                            videodetails['viddes'], 
                            videodetails['vidpblsd'], 
                            videodetails['viddurtin'], 
                            videodetails['vidviwcnt'], 
                            videodetails['vidliks'], 
                            videodetails['vidfavcnt'], 
                            videodetails['vidcmntcnt'])

                    mycursor.execute(insert_video_sql,viddats)

                for commnt in mongoytdata['comment_details']:
                    insert_comment_sql = """INSERT INTO comment_data (channel_id, video_id, comment, author_name, authorchnlid, cmntrply, publishdate)VALUES (%s, %s, %s, %s, %s, %s, %s)"""

                    comment_data = (
                    commnt['channel_id'],
                    commnt['video_id'],
                    commnt['comment'],      
                    commnt['author_name'],
                    commnt['authorchnlid'],
                    commnt['cmntrply'],
                    commnt['publishdate']
                )

                    mycursor.execute(insert_comment_sql, comment_data)



                    mycursor.close()
                    
            else:
              st.warning("No data found select channel.")   
        #else:
         #st.warning("Please select a channel before storing data in SQL.")   
     
# ***Define function to store data in MongoDB 

def datastore_mongo():

      youtubemongo=pymongo.MongoClient("mongodb+srv://rkreddy4895:Rkr2298@rkreddy.nn8dtc8.mongodb.net/?retryWrites=true&w=majority")

      ytdata=youtubemongo["youtubechanneldata"]

      coll=ytdata["youtube_chnl_details"]

      existing_data = coll.find_one(youtubeproject)


      if existing_data:
        print("Data already exist")

      else:
        coll.insert_one(youtubeproject)
        print("Data inserted sucessfully")

      youtubemongo.close()  



option = st.selectbox(
    'Select The Option',
    ('select any option','Get Data and store in Mongodb', 'View Data', 'Migrate To SQL', 'Questions',))



if option == 'Get Data and store in Mongodb':
       user_input=st.text_input('Enter Channel Name', ' ') 
       if user_input:  
            youtubeproject = youtube_chnl_details()
            if youtubeproject:
                storedatainmongo = datastore_mongo()
                st.write(storedatainmongo)
                st.write('Data stored in mongodb successfully')
            else:
              st.write('Data Not Reterive')      
       else:
        st.write('Please enter the valid channel name')    
elif option == 'View Data':
    datainmongo=get_video_datas()
    st.write('Video data:', datainmongo)
elif option == 'Migrate To SQL':
    storesql=data_storein_sql()
    if storesql:
     st.write('Data migrated to SQL successfully')
else:
    st.write('Please select an option')




if option ==  "Questions":
    questions = st.selectbox(
        'what question you want to choose?',
        (   "select the question", "What are the names of all the videos and their corresponding channels?",
        "Which channels have the most number of videos, and how many videos do they have?",
        "What are the top 10 most viewed videos and their respective channels?",
        "How many comments were made on each video, and what are their corresponding video names?",
        "Which videos have the highest number of likes, and what are their corresponding channel names?",
        "What is the total number of likes and dislikes for each video, and what are their corresponding video names?",
        "What is the total number of views for each channel, and what are their corresponding channel names?",
        "What are the names of all the channels that have published videos in the year 2022?",
        "What is the average duration of all videos in each channel, and what are their corresponding channel names?",
        "Which videos have the highest number of comments, and what are their corresponding channel names?"))
    st.write('You selected:', questions)

#Define function to execute queries
    def execute_query(questions):

        conn = mysql.connector.connect(host='localhost',user='root',password='Rkr2298',autocommit=True,auth_plugin='mysql_native_password',charset="utf8mb4")
        mycursor=conn.cursor() 


        mycursor.execute("USE Youtubechanneldetails") 
         
        if questions == "What are the names of all the videos and their corresponding channels?":
                mycursor.execute("select video_Title, channel_name from video_data")
                df = pd.DataFrame(mycursor.fetchall(), columns=["video_Title", "channel_name"])
                st.dataframe(df)  

        
        elif questions == "Which channels have the most number of videos, and how many videos do they have?":
                mycursor.execute("select channel_name,video_count from channel_data order by video_count desc limit 5")
                df = pd.DataFrame(mycursor.fetchall(), columns=["channel_name", "Total_videos"])
                st.dataframe(df)
        
        elif questions == "What are the top 10 most viewed videos and their respective channels?":
                mycursor.execute("select channel_name, video_title, video_viewcount from video_data order by video_viewcount desc limit 10")
                df = pd.DataFrame(mycursor.fetchall(), columns=["channel_name", "video_title", "Viewers"])
                st.dataframe(df)

        elif questions =="How many comments were made on each video, and what are their corresponding video names?":
                mycursor.execute("select channel_name, video_Title,video_comment from video_data order by channel_name,video_Title" )
                df = pd.DataFrame(mycursor.fetchall(), columns=["channel_name", "video_Title", "video_comment"])
                st.dataframe(df)
        
        elif questions == "Which videos have the highest number of likes, and what are their corresponding channel names?":
                mycursor.execute("select channel_name,video_Title,video_likes from video_data order by video_likes desc limit 5")
                df = pd.DataFrame(mycursor.fetchall(), columns=["channel_name", "video_Title", "video_likes"])
                st.dataframe(df)        
        
        elif questions == "What is the total number of likes and dislikes for each video, and what are their corresponding video names?":
                mycursor.execute("select channel_name,video_title,video_likes from video_data order by channel_name ")
                df = pd.DataFrame(mycursor.fetchall(), columns=["channel_name", "video_Title", "video_likes"])
                st.dataframe(df)

        elif questions == "What is the total number of views for each channel, and what are their corresponding channel names?":
                mycursor.execute("select channel_name,channel_views from channel_data order by channel_name")
                df = pd.DataFrame(mycursor.fetchall(), columns=["channel_name", "channel_views"])
                st.dataframe(df)

        elif questions == "What are the names of all the channels that have published videos in the year 2022?":
                mycursor.execute("select channel_name,video_title,video_published from video_data where video_published like '2022%' order by channel_name ")
                df = pd.DataFrame(mycursor.fetchall(), columns=["channel_name", "video_Title", "video_published"])
                st.dataframe(df)

        elif questions == "What is the average duration of all videos in each channel, and what are their corresponding channel names?":
                mycursor.execute("select channel_name, avg(video_duration) from video_data group by channel_name")
                df = pd.DataFrame(mycursor.fetchall(), columns=["channel_name", "average Duration "])
                st.dataframe(df)
       
        elif questions == "Which videos have the highest number of comments, and what are their corresponding channel names?" :
                mycursor.execute("select channel_name,video_Title,video_comment from video_data order by video_comment desc limit 10")
                df = pd.DataFrame(mycursor.fetchall(), columns=["channel_name", "video_Title", "comment_count"])
                st.dataframe(df)
                
    execute_query(questions)  
    st.success("Successfully Done",icon="✅")