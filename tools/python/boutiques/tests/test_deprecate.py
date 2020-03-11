from boutiques.bosh import bosh
from unittest import TestCase
import os
import mock
import json
from boutiques import __file__ as bfile
from boutiques.util.utils import loadJson
from boutiques.deprecate import DeprecateError, deprecate
from boutiques_mocks import MockZenodoRecord,\
    example_boutiques_tool, MockHttpResponse, mock_zenodo_search


def mock_get(*args, **kwargs):

    # Check that URL looks good
    split = args[0].split('/')
    assert(len(split) >= 5)

    command = split[4]
    # Records command
    if command == "records":
        assert(len(split) >= 6)
        record_id = split[10] if len(split) > 6 else split[5]
        if record_id == "00000":
            # Inexistent tool
            return MockHttpResponse(404)
        mock_record1 = example_boutiques_tool
        mock_record1.id = int(record_id)
        if record_id == "22222":
            mock_record1.is_last_version = False
        return mock_zenodo_search([mock_record1])

    # Deposit command
    if command == "deposit":
        # Check auth
        if kwargs.get('params') and kwargs.get('params').get('access_token'):
            return MockHttpResponse(200)
        else:
            return MockHttpResponse(401)


def mock_post(*args, **kwargs):
    # Check that URL looks good
    split = args[0].split('/')
    assert(len(split) >= 5)
    command = split[4]
    # Deposit command
    if command == "deposit":
        json = {"links": {"latest_draft": "plop/coin/pan/12345"},
                "doi": "foo/bar", "files": [{"id": "qwerty"}]}
        if args[0].endswith("actions/publish"):
            return MockHttpResponse(202, json)
        else:
            return MockHttpResponse(201, json)


def mock_delete(*args, **kwargs):
    return MockHttpResponse(204)


def mock_put(*args, **kwargs):
    return MockHttpResponse(200)


def mock_download_deprecated(url, file_path):
    # Mocks the download and save of a deprecated descriptor
    example_1_path = os.path.join(
                        os.path.join(
                            os.path.dirname(bfile), "schema", "examples",
                            "example1", "example1_docker.json"))
    example_1_json = loadJson(example_1_path)
    example_1_json['deprecated-by-doi'] = "a_doi"
    cache_dir = os.path.join(os.path.expanduser('~'), ".cache",
                             "boutiques", "production")
    with open(file_path, 'w') as f:
        f.write(json.dumps(example_1_json))
    return [f.name]


class TestDeprecate(TestCase):

    @mock.patch('requests.get', side_effect=mock_get)
    @mock.patch('requests.post', side_effect=mock_post)
    @mock.patch('requests.put', side_effect=mock_put)
    @mock.patch('requests.delete', side_effect=mock_delete)
    def test_deprecate(self, mock_get, mock_post, mock_put, mock_delete):
        new_doi = bosh(["deprecate", "--verbose", "--by", "zenodo.12345",
                        "zenodo." + str(example_boutiques_tool.id),
                        "--zenodo-token", "hAaW2wSBZMskxpfigTYHcuDrC"
                        "PWr2VeQZgBLErKbfF5RdrKhzzJi8i2hnN8r"])
        self.assertTrue(new_doi)

    @mock.patch('requests.get', side_effect=mock_get)
    @mock.patch('requests.post', side_effect=mock_post)
    @mock.patch('requests.put', side_effect=mock_put)
    @mock.patch('requests.delete', side_effect=mock_delete)
    def test_deprecate_no_by(self, mock_get, mock_post, mock_put, mock_delete):
        new_doi = bosh(["deprecate", "--verbose",
                        "zenodo." + str(example_boutiques_tool.id),
                        "--zenodo-token", "hAaW2wSBZMskxpfigTYHcuDrC"
                        "PWr2VeQZgBLErKbfF5RdrKhzzJi8i2hnN8r"])
        self.assertTrue(new_doi)

    @mock.patch('requests.get', side_effect=mock_get)
    @mock.patch('requests.post', side_effect=mock_post)
    @mock.patch('requests.put', side_effect=mock_put)
    @mock.patch('requests.delete', side_effect=mock_delete)
    def test_deprecate_by_inexistent(self, mock_get, mock_post, mock_put,
                                     mock_delete):
        with self.assertRaises(DeprecateError) as e:
            new_doi = bosh(["deprecate", "--verbose", "--by", "zenodo.00000",
                            "zenodo." + str(example_boutiques_tool.id),
                            "--zenodo-token", "hAaW2wSBZMskxpfigTYHcuDrC"
                            "PWr2VeQZgBLErKbfF5RdrKhzzJi8i2hnN8r"])
        self.assertTrue("Tool does not exist" in str(e.exception))

    @mock.patch('requests.get', side_effect=mock_get)
    @mock.patch('requests.post', side_effect=mock_post)
    @mock.patch('requests.put', side_effect=mock_put)
    @mock.patch('requests.delete', side_effect=mock_delete)
    def test_deprecate_deprecated(self, mock_get, mock_post, mock_put,
                                  mock_delete):
        new_doi = deprecate(zenodo_id="zenodo.11111",
                            sandbox=True,
                            verbose=True,
                            zenodo_token="hAaW2wSBZMskxpfigTYHcuDrC"
                            "PWr2VeQZgBLErKbfF5RdrKhzzJi8i2hnN8r",
                            download_function=mock_download_deprecated)
        self.assertFalse(new_doi)

    @mock.patch('requests.get', side_effect=mock_get)
    @mock.patch('requests.post', side_effect=mock_post)
    @mock.patch('requests.put', side_effect=mock_put)
    @mock.patch('requests.delete', side_effect=mock_delete)
    def test_deprecate_previous_version(self, mock_get, mock_post, mock_put,
                                        mock_delete):
        with self.assertRaises(DeprecateError) as e:
            new_doi = bosh(["deprecate", "--verbose",
                            "zenodo.22222",
                            "--zenodo-token", "hAaW2wSBZMskxpfigTYHcuDrC"
                            "PWr2VeQZgBLErKbfF5RdrKhzzJi8i2hnN8r"])
        self.assertTrue("Tool zenodo.22222 has a newer version"
                        in str(e.exception))
