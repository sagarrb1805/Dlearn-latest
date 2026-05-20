
import pandas as pd
import numpy as np
import skfuzzy as fuzz
# from resource_sample import resources_df

class FuzzyClustering:
    def __init__(self, file_path, n_clusters=6, m=1.4):
        np.random.seed(42)
        self.data_pre = pd.read_csv(file_path)
        self.data = self.data_pre[['aural', 'kinesthetic', 'read/write', 'visual']].values
        # self.learner_ids = self.data_pre['LearnerID'].values  
        self.n_clusters = n_clusters
        self.m = m
        self.cluster_centers = None
        self.membership_matrix = None

        self.train_model()

    def train_model(self):
        
        cntr, u, _, _, _, _, fpc = fuzz.cluster.cmeans(
            self.data.T, c=self.n_clusters, m=self.m, error=0.005, maxiter=1000, init=None
        )
        self.cluster_centers = cntr  
        self.membership_matrix = u   
        print(f"Model trained with FPC value: {fpc}")

    def get_cluster_feature_scores(self, membership_scores):
        if self.cluster_centers is None:
            raise ValueError("Model has not been trained. Call train_model() first.")
        cluster_feature_score = np.dot(membership_scores, self.cluster_centers)
        # return cluster_feature_score
        
        return {
            "Auditory": cluster_feature_score[0],
            "Kinesthetic": cluster_feature_score[1],
            "Read/Write": cluster_feature_score[2],
            "Visual": cluster_feature_score[3]
        }

    def get_existing_learner_membership(self, learner_id):
        if self.membership_matrix is None:
            raise ValueError("Model has not been trained. Call train_model() first.")

        try:
            learner_index = np.where(self.learner_ids == learner_id)[0][0]
        except IndexError:
            return None  

        membership_scores = {f"Cluster {i+1}": self.membership_matrix[i][learner_index] for i in range(self.n_clusters)}
        assigned_cluster_index = np.argmax(self.membership_matrix[:, learner_index]) 

        return {
            "Learner ID": learner_id,
            "Assigned Cluster": f"Cluster {assigned_cluster_index + 1}",
            "Cluster Membership Scores": membership_scores,
            "Cluster Feature Scores": self.get_cluster_feature_scores(membership_scores)  
        }

    def predict_membership_for_new_user(self, user_features):
        if self.cluster_centers is None:
            raise ValueError("Model has not been trained. Call train_model() first.")

        user_features = np.array(user_features).reshape(1, -1)  

        distances = np.linalg.norm(self.cluster_centers - user_features, axis=1) # Euclidean distance

        membership_scores = np.exp(-distances) / np.sum(np.exp(-distances))  

        assigned_cluster_index = np.argmax(membership_scores)  

        return {
            "Learner ID": "New User",
            "Assigned Cluster": f"Cluster {assigned_cluster_index + 1}",
            "Cluster Membership Scores": {f"Cluster {i+1}": membership_scores[i] for i in range(self.n_clusters)},
            "Cluster Feature Scores": self.get_cluster_feature_scores(membership_scores)  
        }

    def get_learner_membership(self, learner_id=None, user_features=None):
      
        if learner_id is not None:
            existing_result = self.get_existing_learner_membership(learner_id)
            if existing_result:
                return existing_result  
        
        if user_features is not None:
            return self.predict_membership_for_new_user(user_features)
        
        return "Error: Provide either a learner ID or user features."




# def filter_resources(learner_profile, resources_df):
  
#     learner_accessibility = set(learner_profile['Accessibility'])  
#     learner_deafness = learner_profile['DeafnessProfile']
#     learner_communication = set(learner_profile['CommunicationMode'])

#     deafness_hierarchy = ['Mild', 'Moderate', 'Severe', 'Profound']
    
    
#     learner_index = deafness_hierarchy.index(learner_deafness)
#     allowed_deafness_levels = deafness_hierarchy[learner_index:]
    
#     filtered_resources = resources_df[
#         resources_df['Accessibility'].apply(lambda x: bool(set(x) & learner_accessibility)) &
#         resources_df['DeafnessSuitability'].apply(lambda x: x in allowed_deafness_levels) &
#         resources_df['CommunicationMode'].apply(lambda x: bool(set(x) & learner_communication))
#     ]
    
#     return filtered_resources




def filter_resources(learner_profile, resources_data):
    # print("learner profile : ", learner_profile)
    # print("resource data: ", resources_data[:2])

    learner_accessibility = set(map(str.lower, learner_profile['Accessibility']))  
    learner_deafness = learner_profile['DeafnessProfile'].lower()
    learner_communication = set(map(str.lower, learner_profile['CommunicationMode']))

    # Deafness hierarchy for filtering
    # deafness_hierarchy = ['mild', 'moderate', 'severe', 'profound']
    # learner_index = deafness_hierarchy.index(learner_deafness)
    # allowed_deafness_levels = deafness_hierarchy[learner_index:]

    resources_df = pd.DataFrame(resources_data, columns=[
        'Title', 'Grade', 'Stream', 'Subject', 'ModuleName', 'Subtopic', 'Description',
        'VideoFilename', 'FileFilename', 'URL', 'ResourceID',
        'Accessibility', 'DeafnessSuitability', 'CommunicationMode', "auditory", "kinethetic", "read_write", "visual", 'id'
    ])
    
    resources_df['Accessibility'] = resources_df['Accessibility'].apply(
        lambda x: [i.lower() for i in x.split(", ")] if isinstance(x, str) and x else []
    )

    resources_df['DeafnessSuitability'] = resources_df['DeafnessSuitability'].apply(
        lambda x: [i.lower() for i in x.split(", ")] if isinstance(x, str) and x else []
    )

    resources_df['CommunicationMode'] = resources_df['CommunicationMode'].apply(
        lambda x: [i.lower() for i in x.split(", ")] if isinstance(x, str) and x else []
    )

   
    filtered_resources = resources_df[
        resources_df['Accessibility'].apply(lambda x: bool(set(x) & learner_accessibility)) &
        resources_df['DeafnessSuitability'].apply(lambda x: learner_deafness in x) &
        resources_df['CommunicationMode'].apply(lambda x: bool(set(x) & learner_communication))
    ]
    # print("Filtered Resources: ", len(filtered_resources))

    filtered_resources_list = [tuple(row) for row in filtered_resources.itertuples(index=False, name=None)]

    return filtered_resources_list



def rank_resources(filtered_resources, learner_prefs):
    if not isinstance(learner_prefs, dict):
        raise ValueError("learner_prefs must be a dictionary with learning style scores.")

    
    columns = [
        'Title', 'Grade', 'Stream', 'Subject', 'ModuleName', 'Subtopic', 'Description',
        'VideoFilename', 'FileFilename', 'URL', 'ResourceID',
        'Accessibility', 'DeafnessSuitability', 'CommunicationMode',
        'Auditory', 'Kinesthetic', 'Read/Write', 'Visual', 'id'
    ]

   
    if not isinstance(filtered_resources, list) or not all(isinstance(item, tuple) for item in filtered_resources):
        raise ValueError("filtered_resources must be a list of tuples.")

    
    try:
        resources_dict_list = [dict(zip(columns, resource)) for resource in filtered_resources]
    except Exception as e:
        raise ValueError(f"Error in converting tuples to dictionary: {e}")

   
    resources_df = pd.DataFrame(resources_dict_list)

    
    numeric_cols = ['Auditory', 'Kinesthetic', 'Read/Write', 'Visual']
    for col in numeric_cols:
        resources_df[col] = pd.to_numeric(resources_df[col], errors='coerce')

    
    def calculate_score(row):
        try:
            weights = np.array([
                learner_prefs['Auditory'],
                learner_prefs['Kinesthetic'],
                learner_prefs['Read/Write'],
                learner_prefs['Visual']
            ])
            resource_values = np.array([
                row['Auditory'],
                row['Kinesthetic'],
                row['Read/Write'],
                row['Visual']
            ])
            # print("calculating weighted sum")
            return np.dot(weights, resource_values)  # Weighted sum
        except KeyError as e:
            raise ValueError(f"Missing key in learner_prefs: {e}")

    
    resources_df['Score'] = resources_df.apply(calculate_score, axis=1)
    
    # ranked_resources = resources_df.sort_values(by="Score", ascending=False)
    resources_df = resources_df.sort_values(by="Score", ascending=False).reset_index(drop=True)
    top_resources = resources_df.iloc[:7]
    remaining = resources_df.iloc[7:].copy()

    samples = []

    if not remaining.empty:
        def dominant_style(row):
            factors = {
                'Auditory': row['Auditory'],
                'Kinesthetic': row['Kinesthetic'],
                'Read/Write': row['Read/Write'],
                'Visual': row['Visual']
            }
            return max(factors, key=factors.get)

        remaining['Bucket'] = remaining.apply(dominant_style, axis=1)
        bucket_scores = remaining.groupby('Bucket')['Score'].mean().sort_values(ascending=False)

        max_sample = 5  
        bucket_sample_counts = {}
        total_buckets = len(bucket_scores)
        for rank, (bucket, avg_score) in enumerate(bucket_scores.items(), start=1):
            sample_size = max(1, max_sample - (rank - 1))  
            bucket_sample_counts[bucket] = sample_size

        for bucket, count in bucket_sample_counts.items():
            group = remaining[remaining['Bucket'] == bucket]
            sampled_group = group.nlargest(count, 'Score')
            samples.append(sampled_group)

    if samples:
        bucketed_resources = pd.concat(samples)
        final_recommendations = pd.concat([top_resources, bucketed_resources])
    else:
        final_recommendations = top_resources

    # final_recommendations = pd.concat([top_resources, bucketed_resources]).sort_values(by="Score", ascending=False).reset_index(drop=True)

    # print("Ranked Resources: ", ranked_resources)
    final_recommendations = final_recommendations.sort_values(by="Score", ascending=False).reset_index(drop=True)
   
    # ranked_resources_list = [tuple(row) for row in final_recommendations.itertuples(index=False, name=None)]
    for col in ['Accessibility', 'DeafnessSuitability', 'CommunicationMode']:
        # Ensure the column exists and handle potential non-list values gracefully
        if col in final_recommendations.columns:
            final_recommendations[col] = final_recommendations[col].apply(
                lambda x: ', '.join(x) if isinstance(x, list) else x
            )
            # Handle potential None/NaN values explicitly if they might appear
            final_recommendations[col] = final_recommendations[col].fillna('')



    original_columns = [
        'Title', 'Grade', 'Stream', 'Subject', 'ModuleName', 'Subtopic', 'Description',
        'VideoFilename', 'FileFilename', 'URL', 'ResourceID',
        'Accessibility', 'DeafnessSuitability', 'CommunicationMode',
        'Auditory', 'Kinesthetic', 'Read/Write', 'Visual', 'id'
    ]

    # Select only the original columns from the final_recommendations DataFrame
    # This creates a new DataFrame with only the desired columns
    filtered_output_df = final_recommendations[original_columns]

    # Convert this filtered DataFrame to a list of tuples
    ranked_resources_list = [tuple(row) for row in filtered_output_df.itertuples(index=False, name=None)]
    
    return ranked_resources_list
    
    return ranked_resources_list







# def rank_resources(filtered_resources, learner_prefs):
    
#     def calculate_score(resource):
#         weights = np.array([learner_prefs['Auditory'], learner_prefs['Kinesthetic'], learner_prefs['Read/Write'], learner_prefs['Visual']])
#         resource_values = np.array([resource['LearningStyles']['Auditory'], resource['LearningStyles']['Kinesthetic'], resource['LearningStyles']['Read/Write'], resource['LearningStyles']['Visual']])
#         return np.dot(weights, resource_values)  
    
#     filtered_resources = filtered_resources.copy()  
#     filtered_resources.loc[:, 'Score'] = filtered_resources.apply(calculate_score, axis=1)

    

#     ranked_resources = filtered_resources.sort_values(by="Score", ascending=False)
    
#     return ranked_resources

if __name__ == "__main__":
    model = FuzzyClustering("../files/ICAADPreprocessed_new.csv", n_clusters=6)


    learner_id = 267
    result = model.get_learner_membership(learner_id=learner_id)
    print("\nExisting Learner Result:", result)


    new_user_features = [0, 0, 1, 1] # [auditory, kinesthetic, read/write, visual]
    new_user_result = model.get_learner_membership(user_features=new_user_features)
    print("\nNew User Result:", new_user_result)



    learner_profile = {
        'Accessibility': ['Captions', 'ISL', 'Voice', "Transcripts"], 
        'DeafnessProfile': 'Profound', 
        'CommunicationMode': ['Sign Supported Speech', 'Speech', "Text"]
    }
    filtered_results = filter_resources(learner_profile, resources_df)
    print("\nfilterd resources: ", filtered_results)

    cluster_feature_score = new_user_result['Cluster Feature Scores']
    # print("\ncluster feature score: ", cluster_feature_score)
    total_weight = sum(cluster_feature_score.values())
    normalized_prefs = {key: val / total_weight for key, val in cluster_feature_score.items()}
    
    print('\nleaner prefs; ', normalized_prefs)

    learner_prefs = {key: float(value) for key, value in normalized_prefs.items()}

    if not filtered_results.empty:
        ranked_resources = rank_resources(filtered_results, learner_prefs)
        print("\nranked resource: ", ranked_resources)
    else: 
        print("No filterd resource found")
    