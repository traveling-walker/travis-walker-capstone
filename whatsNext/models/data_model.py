import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter
import plotly.express as px
from plotly.offline import plot
from .api import get_dict, reset_dict
from whatsNext import cache
from os import path


def get_artist_df():
    artist_df = cache.get("artist_df")
    if artist_df is None:
        artist_df = pd.read_csv(path.join('.', 'data', 'artists.csv'), header=0, low_memory=False,
                                converters={'member_list': lambda x: x[1:-1].split(', '),
                                            'group_list': lambda x: x[1:-1].split(', ')
                                            })
        cache.set("artist_df", artist_df)
    return artist_df


def get_df():
    df = cache.get("df")
    if df is None:
        transform_data(get_dict())
        df = cache.get("df")
    return df


def reset_df():
    reset_dict()
    cache.set("df", None)


def get_pie():
    genre_df = cache.get("genre_df")
    pie = px.pie(values=genre_df['count'], names=genre_df.index)
    pie.update_layout(title_text='Record Collection Breakdown by Genre',
                      title_x=0.5,
                      font_family='Arial'
                      )
    pie_div = plot(pie, output_type='div')
    return pie_div


def get_bar():
    bar = px.bar(cache.get("style_df"), x='style', y='count')
    bar.update_layout(
        title_text='10 Most Frequently Occurring Style Tags',
        title_x=0.5,
        font_family='Arial'
    )
    bar_div = plot(bar, output_type='div')
    return bar_div


def get_hm():
    df = cache.get("df")
    cosine_sim = cache.get("cosine_sim")
    hm = px.imshow(cosine_sim * 100,
                   labels={'color': 'Similarity (%)'},
                   x=df['release_name'],
                   y=df['release_name'],
                   width=800,
                   height=800
                   )
    hm.update_xaxes(showticklabels=False)
    hm.update_yaxes(showticklabels=False)
    hm.update_layout(
        title_text='Heat Map Representing Cosine Similarity Between Albums',
        title_x=0.5,
        font_family='Arial'
    )
    hm_div = plot(hm, output_type='div')
    return hm_div


def get_top_ten():
    return cache.get("top_ten")


def search(string):
    df = cache.get("df")
    matches = df['artist_name'].str.contains(string, case=False) | df['release_name'].str.contains(string, case=False)
    return df[matches]


def clean_string(x):
    if isinstance(x, list):
        return [str.lower(str(i.replace(" ", ""))) for i in x]
    else:
        if isinstance(x, str):
            return str.lower(x.replace(" ", ""))
        else:
            return ''


def create_soup(x):
    return str(x['artist_id']) + ' ' + \
           ' '.join(x['member_list']) + ' ' + \
           ' '.join(x['group_list']) + ' ' + \
           ' '.join(x['genres']) + ' ' +\
           ' '.join(x['styles']) + ' ' +\
           ' '.join(x['descriptors'])


def transform_data(release_dict):
    # Make a DataFrame from the passed in dictionary containing the user's record collection
    # Reset the df's index to and rename the newly made 'index' col to 'release_id'
    df = pd.DataFrame.from_dict(release_dict, orient="index")
    df.reset_index(inplace=True)
    df.rename(columns={'index': 'release_id'}, inplace=True)

    # Make a Pandas series containing release_id's paired with their df index number
    indices = pd.Series(df.index, index=df.release_id)
    cache.set("indices", indices)

    # Clean the genre & style attributes
    df['genres'] = df['genres'].apply(clean_string)
    df['styles'] = df['styles'].apply(clean_string)
    df['descriptors'] = df['descriptors'].apply(clean_string)

    # Merge in the artist_df, so now each release contains band member info (where present)
    df = df.merge(get_artist_df(), how="left", on="artist_id").set_index(df.index)
    df.fillna('', inplace=True)

    # Make the word soup that we will pass into the CountVectorizer
    df['soup'] = df.apply(create_soup, axis=1)

    # Create CountVectorizer, fit_transform the release's word soup attribute,
    # and make a cosine similarity matrix that reflects the likeness between each
    count = CountVectorizer()
    count_matrix = count.fit_transform(df['soup'])
    cosine_sim = cosine_similarity(count_matrix, count_matrix)

    cache.set("df", df)
    cache.set("cosine_sim", cosine_sim)

    analysis(df)


def get_similar(release_id):
    df = cache.get("df")
    # Get the df index that corresponds to the release_id argument
    idx = cache.get("indices")[release_id]

    # Get the release's corresponding artist_id, so we can filter it out of the recommendations
    artist_id = df[df['release_id'] == release_id]['artist_id'].iloc[0]

    # Get the pairwise similarity scores of all albums against our chosen release
    sim_scores = list(enumerate(cache.get("cosine_sim")[idx]))

    # Turn that list of tuples into a Pandas series
    sim_series = pd.Series([i[1] for i in sim_scores])
    sim_series.rename('similarity', inplace=True)

    # Merge the series of similarity scores into the DataFrame containing the full collection
    similar = df.merge(sim_series, how='left', left_index=True, right_index=True)

    # Sort by similariry scores in decending order
    similar.sort_values(by=['similarity'], inplace=True, ascending=False)

    # Filter out any additional albums by the same artist
    similar = similar[similar['artist_id'] != artist_id]

    similar.reset_index(drop=True, inplace=True)

    i = 1
    while i < 10:
        if similar.iloc[i].artist_id in similar[0:i].artist_id.values:
            similar.drop(similar.index[i], inplace=True)
        else:
            i += 1

    # Return the top ten most similar albums
    similar = similar[0:10]
    cache.set("similar", similar)

    return similar


def analysis(df):
    genre_list = []
    for genre in df['genres']:
        for i in genre:
            genre_list.append(i)

    genre_df = pd.DataFrame.from_dict(Counter(genre_list), orient='index', columns=['count'])
    genre_df.sort_values(by=['count'], inplace=True, ascending=False)

    cache.set("genre_df", genre_df)

    style_list = []
    for style in df['styles']:
        for i in style:
            style_list.append(i)

    style_df = pd.DataFrame.from_dict(Counter(style_list), orient='index', columns=['count'])
    style_df.sort_values(by=['count'], inplace=True, ascending=False)
    style_df = style_df[0:10]
    style_df.reset_index(inplace=True)
    style_df.rename(columns={'index': 'style'}, inplace=True)

    cache.set("style_df", style_df)

    top_ten = df['artist_name'].value_counts().head(10)

    cache.set("top_ten", top_ten)
