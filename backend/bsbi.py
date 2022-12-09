"""
Referensi:
[1] https://www.nltk.org/api/nltk.stem.snowball.html
"""

import math
import os
import pickle
from string import punctuation

import nltk
from google.cloud import storage
from nltk import word_tokenize
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer

from index import InvertedIndex
from util import IdMap

storage_client = storage.Client()
bucket = storage_client.bucket("medicalway-be")

root = os.path.dirname(os.path.abspath(__file__))
download_dir = os.path.join(root, 'nltk_data')
os.chdir(download_dir)
nltk.data.path.append(download_dir)

stemmer = SnowballStemmer('english')
stop_words = stopwords.words('english')

punctuation = list(punctuation)


def cleaned_text(file):
    tokenized_words = word_tokenize(file)
    stemmed_words = [stemmer.stem(word) for word in tokenized_words]

    cleaned_tokens = []
    for token in stemmed_words:
        if (token not in stop_words) and (token not in punctuation):
            cleaned_tokens.append(token)

    return cleaned_tokens


class BSBIIndex:
    """
    Attributes
    ----------
    term_id_map(IdMap): Untuk mapping terms ke termIDs
    doc_id_map(IdMap): Untuk mapping relative paths dari dokumen (misal,
                    /collection/0/gamma.txt) to docIDs
    data_dir(str): Path ke data
    output_dir(str): Path ke output index files
    postings_encoding: Lihat di compression.py, kandidatnya adalah StandardPostings,
                    VBEPostings, dsb.
    index_name(str): Nama dari file yang berisi inverted index
    """

    def __init__(self, output_dir, postings_encoding, index_name="main_index"):
        self.term_id_map = IdMap()
        self.doc_id_map = IdMap()
        self.doc_length = dict()
        self.average_doc_length = -1
        self.output_dir = output_dir
        self.index_name = index_name
        self.postings_encoding = postings_encoding
        self.loaded = False

        # Untuk menyimpan nama-nama file dari semua intermediate inverted index
        self.intermediate_indices = []

    def load(self):
        """Memuat doc_id_map and term_id_map dari output directory"""

        with bucket.blob(os.path.join(self.output_dir, 'terms.dict')).open('rb') as f:
            self.term_id_map = pickle.load(f)
        with bucket.blob(os.path.join(self.output_dir, 'docs.dict')).open('rb') as f:
            self.doc_id_map = pickle.load(f)

    def retrieve_bm25(self, query, k=10, k1=1.5, b=0.75):
        """
        Melakukan Ranked Retrieval dengan skema TaaT (Term-at-a-Time).
        Method akan mengembalikan top-K retrieval results.

        w(t, D) = (1 + log tf(t, D))       jika tf(t, D) > 0
                = 0                        jika sebaliknya

        w(t, Q) = IDF = log (N / df(t))

        Score = untuk setiap term di query, akumulasikan w(t, Q) * w(t, D).
                (tidak perlu dinormalisasi dengan panjang dokumen)

        catatan:
            1. informasi DF(t) ada di dictionary postings_dict pada merged index
            2. informasi TF(t, D) ada di tf_li
            3. informasi N bisa didapat dari doc_length pada merged index, len(doc_length)

        Parameters
        ----------
        query: str
            Query tokens yang dipisahkan oleh spasi

            contoh: Query "universitas indonesia depok" artinya ada
            tiga terms: universitas, indonesia, dan depok

        Result
        ------
        List[(int, str)]
            List of tuple: elemen pertama adalah score similarity, dan yang
            kedua adalah nama dokumen.
            Daftar Top-K dokumen terurut mengecil BERDASARKAN SKOR.

        JANGAN LEMPAR ERROR/EXCEPTION untuk terms yang TIDAK ADA di collection.
        :param b:
        :param k1:
        :param query:
        :param k:

        """
        # Load term_id_map dan doc_id_map
        self.load()

        # Struktur: { doc_name: score }
        scores = {}
        cleaned_query = cleaned_text(query)

        with InvertedIndex(self.index_name, self.postings_encoding, directory=self.output_dir) as index:
            for word in cleaned_query:
                if word not in self.term_id_map:
                    continue
                term_id = self.term_id_map[word]

                # IDF = log (N / df(t))
                idf_score = math.log(len(index.doc_length) / index.postings_dict[term_id][1])

                postings_list = index.get_postings_list(term_id)
                for i in range(len(postings_list[0])):
                    doc_id, tf = postings_list[0][i], postings_list[1][i]
                    doc_name = self.doc_id_map[doc_id]

                    # Formula Okapi BM25
                    bm25_score = idf_score
                    bm25_score *= (tf * (k1 + 1))
                    bm25_score /= (k1 * ((1 - b) + b * (index.doc_length[doc_id] / index.avg_doc_length)) + tf)

                    if doc_name not in scores:
                        scores[doc_name] = 0

                    scores[doc_name] = scores[doc_name] + bm25_score

        # Sort berdasarkan nilai score, ubah urutan nama dan skor
        return [(doc_name, score) for (score, doc_name) in
                sorted(scores.items(), key=lambda value: value[1], reverse=True)[:k]]
