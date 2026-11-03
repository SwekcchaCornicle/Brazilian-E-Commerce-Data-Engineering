# Dataset source and attribution

## Primary source

This repository uses the **Brazilian E-Commerce Public Dataset by Olist**:

- Kaggle dataset: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
- Dataset publisher: Olist
- Dataset description: Brazilian e-commerce orders and related entities, including customers, sellers, products, payments, reviews, geolocation, and order items.
- Repository customer source file: [datasets/source/olist_customers_dataset.csv](../datasets/source/olist_customers_dataset.csv)

The repository contains source CSV files from this dataset. The customer pipeline focuses on the customer dataset and maps these columns:

| Olist source column | Pipeline field |
|---|---|
| `customer_id` | `customer_id` |
| `customer_unique_id` | `customer_unique_id` |
| `customer_zip_code_prefix` | `customer_zip_code_prefix` (preserved as a string to keep leading zeroes) |
| `customer_city` | `customer_city` |
| `customer_state` | `customer_state` |

The Lambda ingestion contract currently requires `customer_id`, `customer_city`, and `customer_state`. The unique customer ID and ZIP prefix are retained as additional customer attributes when present. The committed two-record five-field JSON fixture is synthetic test data, not an actual Kaggle row.

## Download

Download the dataset from Kaggle using the dataset page above. Kaggle may require a signed-in account and acceptance of the dataset's terms. Follow the license and usage terms shown on the Kaggle dataset page; do not assume that a public download means unrestricted reuse.

## Reproducibility note

The live AWS tests described in this repository also use small synthetic JSON fixtures (`terraform/valid_customer.json` and `terraform/invalid_customer.json`) to test valid and invalid paths. Those fixtures are not the full Kaggle dataset.

For repeatable experiments, record the dataset download date and the exact files used. Avoid committing credentials, Kaggle API tokens, or personal data.
