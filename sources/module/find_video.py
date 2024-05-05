from bs4 import BeautifulSoup


def find_video_links(html_filename):
    result = []
    with open(html_filename, 'br') as html_file:
        html = html_file.read()
    try:
        soup = BeautifulSoup(html, 'lxml')
        story = soup.find('div', class_='page-story__story')
        players = story.find_all('div', {'class': 'player', 'data-type': 'video-file'})
    except:
        players = []
    for player in players:
        # result.append(player.get('data-source')+'.mp4')
        
        data_source = 'data-source'
        data_story_id = 'data-story-id'
        data_duration = 'data-duration'
        data_mp4_size = 'data-mp4-size'
        res = {
            data_source: player.get(data_source),
            data_story_id: player.get(data_story_id),
            data_duration: player.get(data_duration),
            data_mp4_size: player.get(data_mp4_size)
        }
        result.append(res)

    return result